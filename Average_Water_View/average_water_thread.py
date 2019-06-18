from PyQt5.QtCore import QThread, QEvent, pyqtSignal, QMutex, QWaitCondition
import collections
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn
import logging
import csv
import datetime
from threading import Event, Thread
import multiprocessing
import os
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import time
import matplotlib.pyplot as plt
#from . import plot_data_thread, plot_earth_vel_east_thread, plot_earth_vel_north_thread
import ntpath


class AverageWaterThread(QThread):

    increment_ens_sig = pyqtSignal(int)
    avg_taken_sig = pyqtSignal(object)
    refresh_wave_height_web_view_sig = pyqtSignal()
    refresh_earth_east_vel_web_view_sig = pyqtSignal()
    refresh_earth_north_vel_web_view_sig = pyqtSignal()
    refresh_mag_web_view_sig = pyqtSignal()
    refresh_dir_web_view_sig = pyqtSignal()

    def __init__(self, rti_config):
        QThread.__init__(self)

        self.rti_config = rti_config
        self.thread_alive = True
        self.event = Event()
        self.mutex = QMutex()

        self.ens_queue = collections.deque()

        self.csv_file_path = ""
        self.csv_file_index = 1
        self.csv_creation_date = datetime.datetime.now()
        self.CSV_FILE_EXT = ".csv"

        self.output_dir = self.rti_config.config['AWC']['output_dir'] + os.sep

        self.wave_height_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "WaveHeight.html"
        self.earth_east_vel_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel_East.html"
        self.earth_north_vel_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel_North.html"
        self.mag_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "Magnitude.html"
        self.dir_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "Direction.html"

        # Dictionary to hold all the average water column objects
        self.awc_dict = {}

        # Latest Average Water Column count
        self.avg_counter = 0

        self.df_columns = ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "blank", "bin_size", "value"]
        #self.awc_df = pd.DataFrame()

    def shutdown(self):
        self.thread_alive = False
        self.event.set()



    def update_earth_east_vel_plot(self):
        self.refresh_earth_east_vel_web_view_sig.emit()

    def update_earth_north_vel_plot(self):
        self.refresh_earth_north_vel_web_view_sig.emit()

    def update_wave_height_plot(self):
        self.refresh_wave_height_web_view_sig.emit()

    def update_mag_plot(self):
        self.refresh_mag_web_view_sig.emit()

    def update_dir_plot(self):
        self.refresh_dir_web_view_sig.emit()

    def add_ens(self, ens):
        """
        Add an ensemble to this view model.

        This will accumulate the ensemble in the Average Water Column
        objects in a dictionary.  When the correct number of ensembles
        have been accumulated, the average will be taken.
        :param ens: Ensemble to accumulate.
        :return:
        """

        # Add data to the queue
        self.ens_queue.append(ens)

        # Wakeup the thread
        self.event.set()

    def reset_average(self):
        """
        Reset the counters and reset all the
        AverageWaterColumn in the dictionary.
        :return:
        """
        # Reset the counter
        self.avg_counter = 0

        # Reset all the AWC in the dictionary
        for awc_key in self.awc_dict.keys():
            self.awc_dict[awc_key].reset()

        # Clear the dataframe
        #self.awc_df = pd.DataFrame(columns=self.awc_df.columns)

    def run(self):
        """
        Process the thread.
        Remove any data from the queue.
        Then accumulate the ensemble.
        If enough ensembles have been accumulate, average and display the data.
        :return:
        """

        while self.thread_alive:

            # Wait to be woken up
            self.event.wait()

            # Clear automatically
            self.event.clear()

            while len(self.ens_queue) > 0:
                # Remove the ensemble from the queue
                ens = self.ens_queue.popleft()

                # Check if we need to average
                if int(self.rti_config.config['AWC']['num_ensembles']) > 1:
                    # Accumulate the water column data
                    self.accumulate_ens(ens)

                    # Check if it is time to average data
                    if self.avg_counter >= int(self.rti_config.config['AWC']['num_ensembles']):
                        self.average_and_display()
                else:
                    # Not averaging the data, so just write to CSV and display data
                    self.no_average_and_display(ens)

    def accumulate_ens(self, ens):
        """
        Accumulate the ensemble data.
        If a dictionary entry does not exist,
        create a dictionary entry.  Then create an
        Average Water Column and store it in the dictionary.

        Then add the ensemble to the Average Water Column.
        :param ens: Ensemble to accumulate.
        :return:
        """
        if ens:
            # Get the key from the ensemble
            # If none is returned, then the ensemble does not have the Ensemble Data Set
            key = self.gen_dict_key(ens)

            if key:
                # Increment the counter
                self.avg_counter += 1

                # Get the average water column object from dict if exist
                # If it does not exist, create the entry
                # Then add the ensemble to the list
                if key not in self.awc_dict:
                    self.awc_dict[key] = AverageWaterColumn(int(self.rti_config.config['AWC']['num_ensembles']),
                                                            ens.EnsembleData.SysFirmwareSubsystemCode,
                                                            ens.EnsembleData.SubsystemConfig)

                # Add the ensemble to the correct AverageWaterColumn
                self.awc_dict[key].add_ens(ens)

                # Emit a signal that an ensemble was added
                #self.increment_ens_sig.emit(self.avg_counter)

    def gen_dict_key(self, ens):
        """
        Generate a dictionary key from the subsystem code and
        subsystem configuration.
        [ssCode_ssConfig]
        :param ens: Ensemble to get the informaton
        :return:
        """
        if ens.IsEnsembleData:
            ss_code = ens.EnsembleData.SysFirmwareSubsystemCode
            ss_config = ens.EnsembleData.SubsystemConfig
            return str(str(ss_code) + "_" + str(ss_config))
        else:
            return None

    def no_average_and_display(self, ens):
        """
        We need to still display the data and write the CSV file, but we are
        not averaging.  The settings is set to 1 for the number of ensembles
        to average.
        :param ens: Ensemble to process.
        :return:
        """
        if ens:
            # Generate the CSV date for the file
            csv_data, df_data = self.generate_csv_data_no_avg(ens)

            # Update CSV file
            self.write_csv_file(csv_data)

            # Create dataframe
            df = pd.DataFrame(df_data, columns=self.df_columns)
            df['datetime'] = pd.to_datetime(df['datetime'])

            # Emit signal that average taken
            # so file list can be updated
            self.avg_taken_sig.emit(df)

    def average_and_display(self):
        """
        Average the data and display the data.
        :return:
        """
        accum_df = pd.DataFrame([], columns=self.df_columns)

        for awc_key in self.awc_dict.keys():
            # Average the data
            awc_average = self.awc_dict[awc_key].average()

            # Generate the CSV date for the file
            csv_data, df_data = self.generate_csv_data(awc_average, awc_key)

            # Update CSV file
            self.write_csv_file(csv_data)

            # Update the dataframe
            df = pd.DataFrame(df_data, columns=self.df_columns)
            if accum_df.empty:
                #self.awc_df = df
                #self.awc_df['datetime'] = pd.to_datetime(self.awc_df['datetime'])

                accum_df = df
                accum_df['datetime'] = pd.to_datetime(accum_df['datetime'])
            else:
                #self.awc_df = self.awc_df.append(df)
                accum_df = accum_df.append(df)

        # Create the plot from the CSV file
        # The CSV file is complete
        #self.display_data_from_file(self.csv_file_path)

        # Reset the counter
        self.avg_counter = 0

        # Sort the data by date and time
        accum_df.sort_values(by=['datetime'], inplace=True)

        # Emit signal that average taken
        # so file list can be updated
        if not accum_df.empty:
            self.avg_taken_sig.emit(accum_df)

        # Display the data
        #self.display_data(self.awc_df)

    def display_data(self, awc_df):
        """
        Display the data given the dataframe.
        This will pass all the data to the plot threads.
        :param awc_df: Dataframe to plot.
        :return:
        """
        # Display data
        # Add the data to the plot threads
        self.thread_wave_height_display.add(self.awc_df)
        self.thread_earth_east_display.add(self.awc_df)
        self.thread_earth_north_display.add(self.awc_df)
        self.thread_mag_display.add(self.awc_df)
        self.thread_dir_display.add(self.awc_df)

    def get_file_name(self, path):
        """
        Get just the file name.
        Then remove the file extension.
        :param path: File path.
        :return: File name without path or extension
        """
        head, tail = ntpath.split(path)
        file_name_w_ext = tail or ntpath.basename(head)
        return os.path.splitext(file_name_w_ext)[0]

    def generate_csv_data(self, awc_avg, awc_key):
        """
        Write all the CSV data.
        :param awc_avg: Average Velocity data
        :param awc_key: Key to identify the subsystem and config.
        :return:
        """
        csv_rows = []
        df_datas = []
        # Earth Velocity data
        if awc_avg[AverageWaterColumn.INDEX_EARTH]:
            csv_row, df_data = self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_EARTH],              # Earth Velocity data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_EARTH_VEL,                               # Data Type CSV Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last time in average
            csv_rows += csv_row
            df_datas += df_data
        # Mag Data
        if awc_avg[AverageWaterColumn.INDEX_MAG]:
            csv_row, df_data = self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_MAG],                # Mag data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_MAG,                                     # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last time in average
            csv_rows += csv_row
            df_datas += df_data
        # Dir Data
        if awc_avg[AverageWaterColumn.INDEX_DIR]:
            csv_row, df_data = self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_DIR],                # Dir Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_DIR,                                     # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average
            csv_rows += csv_row
            df_datas += df_data

        # Pressure Data
        if awc_avg[AverageWaterColumn.INDEX_PRESSURE]:
            csv_row, df_data = self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_PRESSURE],           # Pressure Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_PRESSURE,                                # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average
            csv_rows += csv_row
            df_datas += df_data

        # Transducer Depth Data
        if awc_avg[AverageWaterColumn.INDEX_XDCR_DEPTH]:
            csv_row, df_data = self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_XDCR_DEPTH],         # Transducer Depth Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_XDCR_DEPTH,                              # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average
            csv_rows += csv_row
            df_datas += df_data

        return csv_rows, df_datas

    def generate_csv_data_no_avg(self, ens):
        """
        Generate the CSV and Dataframe data from the ensemble.
        This is only called if the user is not averaging the data.
        :param ens: Ensemble data
        :return:
        """
        csv_rows = []
        df_datas = []

        dt = datetime.datetime.now()
        ss_code = 0
        ss_config = 0
        blank = 0.0
        bin_size = 0.0

        if ens.IsEnsembleData:
            dt = ens.EnsembleData.datetime()
            ss_code = ens.EnsembleData.SysFirmwareSubsystemCode
            ss_config = ens.EnsembleData.SubsystemConfig

        if ens.IsAncillaryData:
            blank = ens.AncillaryData.FirstBinRange
            bin_size = ens.AncillaryData.BinSize
            pressure = ens.AncillaryData.Pressure
            xdcr_depth = ens.AncillaryData.TransducerDepth

            # Pressure
            csv_rows.append([Ensemble.gen_csv_line(dt, Ensemble.CSV_PRESSURE, ss_code, ss_config, 0, 0, blank, bin_size, pressure)])
            df_datas.append([dt, Ensemble.CSV_PRESSURE, ss_code, ss_config, 0, 0, blank, bin_size, pressure])

            # Transducer Depth
            csv_rows.append([Ensemble.gen_csv_line(dt, Ensemble.CSV_XDCR_DEPTH, ss_code, ss_config, 0, 0, blank, bin_size, xdcr_depth)])
            df_datas.append([dt, Ensemble.CSV_XDCR_DEPTH, ss_code, ss_config, 0, 0, blank, bin_size, xdcr_depth])

        if ens.IsEarthVelocity:
            csv_rows += (ens.EarthVelocity.encode_csv(dt, ss_code, ss_config, blank, bin_size))
            df_datas += (ens.EarthVelocity.encode_df(dt, ss_code, ss_config, blank, bin_size))

        return csv_rows, df_datas

    def write_csv_file(self, csv_rows):
        """
        Write the CSV file.  This will write all the lines
        given to the CSV file.
        :param csv_rows: Rows to add to the CSV file.
        :return:
        """
        try:
            # Get the latest file path or create one
            self.csv_file_path = self.check_or_create_file()

            # Write the data to the CSV file
            # Added newline='' to ensure no extra lines included
            with open(self.csv_file_path, 'a', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_NONE, escapechar=' ')

                # Write the data
                wr.writerows(csv_rows)

        except PermissionError as pe:
            logging.error("File in use.  Permission error.  ", pe)
        except Exception as e:
            logging.error("Error writing to the CSV file.  ", e)

    def get_csv_data(self, data, awc_key, data_type, last_time):
        """
        Append the data to the CSV file.

        Ex:
        ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "blank", "bin_size", "value"]
        2019/02/23 15:23:22.56, EARTH_VEL, 4, 1, 2, 2, 7.5, 1.245

        :param data: Data for all beams.
        :param awc_key: Key used to give the file an identifier for the subsystem and config.
        :param data_type: Data type to place into the csv line.
        :param last_time: Last time in the average.
        :return:
        """

        # Get the parameters for the data
        blank = self.awc_dict[awc_key].blank
        bin_size = self.awc_dict[awc_key].bin_size
        ss_code = self.awc_dict[awc_key].ss_code
        ss_config = self.awc_dict[awc_key].ss_config

        # Use the current time as a backup
        #dt_time = datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S:%f')
        dt_time = datetime.datetime.now()
        if last_time:
            dt_time = last_time

        # Get the data
        bin_num = 1
        beam_num = 0
        row_data = []
        df_data = []

        # Go through each bin and add a line to the csv file
        for bin_data in data:
            if type(bin_data) == list:
                beam_num = 0
                for beam_data in bin_data:
                    val = beam_data
                    row_data.append([(Ensemble.gen_csv_line(dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, val))])
                    df_data.append([dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, val])
                    beam_num += 1
            else:
                row_data.append([(Ensemble.gen_csv_line(dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, bin_data))])
                df_data.append([dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, bin_data])

            # Increment the bin number
            bin_num += 1

        return row_data, df_data

    def check_or_create_file(self):
        """

        Check if the file exceeds the time limit.  If the time limit is met,
        create a new file.

        Check if the file exist.  If it does not exist,
        create the file.

        Create a new file if the file exceeds 16mb.

        Add a header to the new file.

        File name
        /path/to/A00002.csv
        :return:
        """
        # Flag if a new file was created
        # If a new file is created, then the average file should create the plots
        new_file_flag = False
        csv_index_prev_file = self.csv_file_index

        # Get the max file size in bytes
        max_file_size = int(self.rti_config.config['AWC']['max_file_size']) * 1048576

        # Check the date the file was created
        # Create a new file if hour exceeds the limit
        csv_max_hours = float(self.rti_config.config['AWC']['csv_max_hours'])
        csv_dt = datetime.timedelta(hours=csv_max_hours)

        if datetime.datetime.now() > self.csv_creation_date + csv_dt:
            # Flag that a new file is being created
            new_file_flag = True
            csv_index_prev_file = self.csv_file_index

            # Create a new file
            self.csv_file_index += 1

        # Create the file name
        file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        # Look if the file exist, if it does, make sure it is less than max file size
        while os.path.isfile(file_path) and os.path.getsize(file_path) >= max_file_size:
            new_file_flag = True
            csv_index_prev_file = self.csv_file_index

            # Create new file path
            self.csv_file_index += 1
            file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        # If the file does not exist, create it
        if not os.path.exists(file_path):
            header = ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "bin_depth", "value"]

            # Open the file and write the header to the row
            with open(file_path, 'w', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)
                wr.writerow(header)

                # Set the creation time
                self.csv_creation_date = datetime.datetime.now()

        # Create the plots from the old
        #if new_file_flag:
        #    old_file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(csv_index_prev_file).zfill(5) + self.CSV_FILE_EXT
        #    thread_plots_csv = Thread(target=self.display_data_from_file, args=[old_file_path, ])
        #    thread_plots_csv.start()

        return file_path
