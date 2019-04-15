from PyQt5.QtCore import QThread, QEvent, pyqtSignal
import collections
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn
import logging
import csv
import datetime
import os
import pandas as pd


class AverageWaterThread(QThread):

    increment_ens_sig = pyqtSignal(int)
    avg_taken_sig = pyqtSignal()

    def __init__(self, rti_config):
        QThread.__init__(self)

        self.rti_config = rti_config
        self.thread_alive = True
        self.event = QEvent()

        self.ens_queue = collections.deque()

        self.csv_file_path = ""
        self.csv_file_index = 1
        self.csv_creation_date = datetime.datetime.now()
        self.CSV_FILE_EXT = ".csv"

        # Dictionary to hold all the average water column objects
        self.awc_dict = {}

        # Latest Average Water Column
        self.avg_counter = 0

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

        # Emit a signal that an ensemble was added
        #self.increment_ens_sig.emit(self.avg_counter)

        # Wakeup the thread
        self.event.set()

    def run(self):

        while self.thread_alive:

            # Wait to be woken up
            self.event.wait()

            while len(self.ens_queue) > 0:
                # Remove the ensemble from the queue
                ens = self.ens_queue.popleft()

                # Accumulate the water column data
                self.accumulate_ens(ens)

                # Check if it is time to average data
                if self.avg_counter >= int(self.rti_config.config['AWC']['num_ensembles']):
                    self.average_and_display()

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
                self.increment_ens_sig.emit(self.avg_counter)

    def average_and_display(self):
        """
        Average the data and display the data.
        :return:
        """
        for awc_key in self.awc_dict.keys():
            # Average the data
            awc_average = self.awc_dict[awc_key].average()

            # Update CSV file
            self.write_csv(awc_average, awc_key)

        # Reset the counter
        self.avg_counter = 0

        # Emit signal that average taken
        # so file list can be updated
        self.avg_taken_sig.emit()

        # Display data
        self.display_data()

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

    def display_data(self):

        # Read in the CSV data of the average data
        avg_df = pd.read_csv(self.csv_file_path)

        # Set the datetime column values as datetime values
        avg_df['datetime'] = pd.to_datetime(avg_df['datetime'])
        #avg_df = avg_df.set_index('datetime')
        #avg_df.drop(['datetime'], axis=1, inplace=True)

        # Sort the data by date and time
        avg_df = avg_df.sort_index()

        # Create a thread to plot the height
        #self.plot_wave_height(avg_df)

        # Update the Earth Vel Plot East
        #self.plot_earth_vel(avg_df,
        #                    0,
        #                    int(self.rti_config.config['Waves']['selected_bin_1']),
        #                    int(self.rti_config.config['Waves']['selected_bin_2']),
        #                    int(self.rti_config.config['Waves']['selected_bin_3']))

    def write_csv(self, awc_avg, awc_key):
        """
        Write all the CSV data.
        :param awc_avg: Average Velocity data
        :param awc_key: Key to identify the subsystem and config.
        :return:
        """
        csv_rows = []
        # Earth Velocity data
        if awc_avg[AverageWaterColumn.INDEX_EARTH]:
            csv_rows += self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_EARTH],              # Earth Velocity data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_EARTH_VEL,                               # Data Type CSV Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last time in average
        # Mag Data
        if awc_avg[AverageWaterColumn.INDEX_MAG]:
            csv_rows += self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_MAG],                # Mag data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_MAG,                                     # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last time in average
        # Dir Data
        if awc_avg[AverageWaterColumn.INDEX_DIR]:
            csv_rows += self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_DIR],                # Dir Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_DIR,                                     # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average

        # Pressure Data
        if awc_avg[AverageWaterColumn.INDEX_PRESSURE]:
            csv_rows += self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_PRESSURE],           # Pressure Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_PRESSURE,                                # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average

        # Transducer Depth Data
        if awc_avg[AverageWaterColumn.INDEX_XDCR_DEPTH]:
            csv_rows += self.get_csv_data(awc_avg[AverageWaterColumn.INDEX_XDCR_DEPTH],         # Transducer Depth Data average
                                          awc_key,                                              # Key for subsystem code and config
                                          Ensemble.CSV_XDCR_DEPTH,                              # Data Type Title
                                          awc_avg[AverageWaterColumn.INDEX_LAST_TIME])          # Last  time in average

        # Write the accumulated rows to the file
        self.write_csv_file(csv_rows)

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
        ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "bin_depth", "value"]
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

        # Go through each bin and add a line to the csv file
        for bin_data in data:
            if type(bin_data) == list:
                beam_num = 0
                for beam_data in bin_data:
                    val = beam_data
                    row_data.append([(Ensemble.gen_csv_line(dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, val))])
                    beam_num += 1
            else:
                row_data.append([(Ensemble.gen_csv_line(dt_time, data_type, ss_code, ss_config, bin_num, beam_num, blank, bin_size, bin_data))])

            # Increment the bin number
            bin_num += 1

        return row_data

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
        # Get the max file size in bytes
        max_file_size = int(self.rti_config.config['AWC']['max_file_size']) * 1048576

        # Check the date the file was created
        # Create a new file if hour exceeds the limit
        csv_max_hours = float(self.rti_config.config['AWC']['csv_max_hours'])
        csv_dt = datetime.timedelta(hours=csv_max_hours)
        #if csv_max_hours < 1:
        #    csv_dt = datetime.timedelta(minutes=(csv_max_hours * 60))

        if datetime.datetime.now() > self.csv_creation_date + csv_dt:
            # Create a new file
            self.csv_file_index += 1

        # Create the file name
        file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        # Look if the file exist, if it does, make sure it is less than max file size
        while os.path.isfile(file_path) and os.path.getsize(file_path) >= max_file_size:
            self.csv_file_index += 1
            file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        # If the file des not exist, create it
        if not os.path.exists(file_path):
            header = ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "bin_depth", "value"]

            # Open the file and write the header to the row
            with open(file_path, 'w', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)
                wr.writerow(header)

                # Set the creation time
                self.csv_creation_date = datetime.datetime.now()

        return file_path