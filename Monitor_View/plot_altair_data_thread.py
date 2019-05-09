from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import time
import os
import logging
from threading import Event
from collections import deque
import ntpath
import altair as alt


class PlotDataThread(QThread):
    """
    Plot the data using a QThread.
    """

    PLOT_TYPE_WAVE_HEIGHT = "WaveHeight"
    PLOT_TYPE_EARTH_EAST = "EarthEast"
    PLOT_TYPE_EARTH_NORTH = "EarthNorth"
    PLOT_TYPE_MAG = "Magnitude"
    PLOT_TYPE_DIR = "Direction"

    refresh_web_view_sig = pyqtSignal()

    def __init__(self, rti_config, plot_type, plot_html_path):
        QThread.__init__(self)

        self.rti_config = rti_config
        self.plot_type = plot_type
        self.setObjectName("Plot Thread: " + plot_type)
        self.html_file = plot_html_path

        self.thread_event = Event()
        self.queue = deque()
        self.thread_alive = True

    def shutdown(self):
        """
        Shutdown the object.
        :return:
        """
        self.thread_alive = False
        self.thread_event.set()

    def add(self, avg_df):
        """
        Add data to the queue.  Then wakeup the thread and plot the data.
        :param avg_df: Data to add to the queue and plot
        :return:
        """
        # Add the data to the queue and wakeup the thread
        self.queue.append(avg_df)

        # Wakeup the thread
        self.thread_event.set()

    def run(self):
        """
        Process the data in the queue.
        :return:
        """
        while self.thread_alive:

            # Sleep until data is added to the queue
            self.thread_event.wait()

            # Process data in the queue
            # Only use the last data in the queue, because it is accumulating data anyway
            avg_df = pd.DataFrame()
            while len(self.queue) > 0:

                # Remove the df from the queue and plot
                avg_df = self.queue.popleft()

                # Check if thread is alive, this may be delayed
                if not self.thread_alive:
                    return

            start = time.clock()
            if not avg_df.empty:
                # Determine the plot type
                if self.plot_type == PlotDataThread.PLOT_TYPE_WAVE_HEIGHT:
                    self.plot_wave_height(avg_df)
                if self.plot_type == PlotDataThread.PLOT_TYPE_EARTH_EAST:
                    self.plot_earth_vel_east(avg_df,
                                             int(self.rti_config.config['Waves']['selected_bin_1']),
                                             int(self.rti_config.config['Waves']['selected_bin_2']),
                                             int(self.rti_config.config['Waves']['selected_bin_3']))
                if self.plot_type == PlotDataThread.PLOT_TYPE_EARTH_NORTH:
                    self.plot_earth_vel_north(avg_df,
                                              int(self.rti_config.config['Waves']['selected_bin_1']),
                                              int(self.rti_config.config['Waves']['selected_bin_2']),
                                              int(self.rti_config.config['Waves']['selected_bin_3']))
                if self.plot_type == PlotDataThread.PLOT_TYPE_MAG:
                    self.plot_magnitude(avg_df,
                                        int(self.rti_config.config['Waves']['selected_bin_1']),
                                        int(self.rti_config.config['Waves']['selected_bin_2']),
                                        int(self.rti_config.config['Waves']['selected_bin_3']))
                if self.plot_type == PlotDataThread.PLOT_TYPE_DIR:
                    self.plot_direction(avg_df,
                                        int(self.rti_config.config['Waves']['selected_bin_1']),
                                        int(self.rti_config.config['Waves']['selected_bin_2']),
                                        int(self.rti_config.config['Waves']['selected_bin_3']))
            logging.warning("Plot Time [" + self.plot_type + "]: " + str(time.clock()-start))

            self.thread_event.clear()

    def plot_wave_height(self, avg_df):
        """
        Create a HTML plot of the wave height data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :return:
        """
        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[avg_df.data_type.str.contains("XdcrDepth")]

        plot = alt.Chart(selected_avg_df).mark_line().encode(
            alt.X('datetime:T', title='Date'),
            alt.Y('value:Q', title='Height (m)'),
            tooltip=['datetime:T', 'value:Q']
        ).properties(title="Wave Height",
                     width=800,
                     height=600).interactive()

        plot.save(self.html_file)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def plot_earth_vel_east(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Earth Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :param selected_bin_1: Selected Bin 1.
        :param selected_bin_2: Selected Bin 2.
        :param selected_bin_3: Selected Bin 3.
        :return:
        """
        # Selected Bins
        selected_bins = [selected_bin_1, selected_bin_2, selected_bin_3]

        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.beam_num == 0) & (avg_df.bin_num.isin(selected_bins))]

        plot = alt.Chart(selected_avg_df).mark_line().encode(
            alt.X('datetime:T', title='Date'),
            alt.Y('value:Q', title='Velocity (m/s)'),
            color='bin_num:N',
            tooltip=['datetime:T', 'value:Q']
        ).properties(title="Earth Velocity East",
                     width=800,
                     height=600).interactive()

        plot.save(self.html_file)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def plot_earth_vel_north(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Earth Velocity North data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :param selected_bin_1: Selected Bin 1.
        :param selected_bin_2: Selected Bin 2.
        :param selected_bin_3: Selected Bin 3.
        :return:
        """
        # Selected Bins
        selected_bins = [selected_bin_1, selected_bin_2, selected_bin_3]

        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.beam_num == 1) & (avg_df.bin_num.isin(selected_bins))]

        plot = alt.Chart(selected_avg_df).mark_line().encode(
            alt.X('datetime:T', title='Date'),
            alt.Y('value:Q', title='Velocity (m/s)'),
            color='bin_num:N',
            tooltip=['datetime:T', 'value:Q', 'bin_num:N']
        ).properties(title="Earth Velocity North",
                     width=800,
                     height=600).interactive()

        plot.save(self.html_file)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def plot_magnitude(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Magnitude Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :param selected_bin_1: Selected Bin 1.
        :param selected_bin_2: Selected Bin 2.
        :param selected_bin_3: Selected Bin 3.
        :return:
        """
        # Selected Bins
        selected_bins = [selected_bin_1, selected_bin_2, selected_bin_3]

        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("Magnitude")) & (avg_df.beam_num == 0) & (avg_df.bin_num.isin(selected_bins))]

        plot = alt.Chart(selected_avg_df).mark_line().encode(
            alt.X('datetime:T', title='Date'),
            alt.Y('value:Q', title='Velocity (m/s)'),
            color='bin_num:N',
            tooltip=['datetime:T', 'value:Q', 'bin_num:N']
        ).properties(title="Water Velocity Magnitude",
                     width=800,
                     height=600).interactive()

        plot.save(self.html_file)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def plot_direction(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Magnitude Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :param selected_bin_1: Selected Bin 1.
        :param selected_bin_2: Selected Bin 2.
        :param selected_bin_3: Selected Bin 3.
        :return:
        """
        # Selected Bins
        selected_bins = [selected_bin_1, selected_bin_2, selected_bin_3]

        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("Direction")) & (avg_df.beam_num == 0) & (avg_df.bin_num.isin(selected_bins))]

        plot = alt.Chart(selected_avg_df).mark_line().encode(
            alt.X('datetime:T', title='Date'),
            alt.Y('value:Q', title='Direction (degrees)'),
            color='bin_num:N',
            tooltip=['datetime:T', 'value:Q', 'bin_num:N']
        ).properties(title="Water Direction",
                     width=800,
                     height=600).interactive()

        plot.save(self.html_file)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    @staticmethod
    def plot_data_from_file(csv_file_path, rti_config):
        """
        Generate plots from the CSV file selected.
        :param csv_file_path: CSV file to generate the plots.
        :param rti_config: RTI Config to get the settings.
        :return:
        """
        if os.path.exists(csv_file_path):
            # Read in the CSV data of the average data
            avg_df = pd.read_csv(csv_file_path)

            # Set the datetime column values as datetime values
            avg_df['datetime'] = pd.to_datetime(avg_df['datetime'])

            # Sort the data by date and time
            avg_df.sort_values(by=['datetime'], inplace=True)

            # Get the CSV file name without the extension and root dir
            head, tail = ntpath.split(csv_file_path)
            file_name_w_ext = tail or ntpath.basename(head)
            csv_file_name = os.path.splitext(file_name_w_ext)[0]

            wave_height_html_file = rti_config.config['AWC']['output_dir'] + os.sep + "WaveHeight_" + csv_file_name + ".html"
            earth_east_vel_html_file = rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel_East_" + csv_file_name + ".html"
            earth_north_vel_html_file = rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel_North_" + csv_file_name + ".html"
            mag_html_file = rti_config.config['AWC']['output_dir'] + os.sep + "Magnitude_" + csv_file_name + ".html"
            dir_html_file = rti_config.config['AWC']['output_dir'] + os.sep + "Direction_" + csv_file_name + ".html"

            # Display the data
            thread_wave_height_display = PlotDataThread(rti_config, PlotDataThread.PLOT_TYPE_WAVE_HEIGHT, wave_height_html_file)
            thread_wave_height_display.start()

            thread_earth_east_display = PlotDataThread(rti_config, PlotDataThread.PLOT_TYPE_EARTH_EAST, earth_east_vel_html_file)
            thread_earth_east_display.start()

            thread_earth_north_display = PlotDataThread(rti_config, PlotDataThread.PLOT_TYPE_EARTH_NORTH, earth_north_vel_html_file)
            thread_earth_north_display.start()

            thread_mag_display = PlotDataThread(rti_config, PlotDataThread.PLOT_TYPE_MAG, mag_html_file)
            thread_mag_display.start()

            thread_dir_display = PlotDataThread(rti_config, PlotDataThread.PLOT_TYPE_DIR, dir_html_file)
            thread_dir_display.start()

            # Add the data to the plot threads
            thread_wave_height_display.add(avg_df)
            thread_earth_east_display.add(avg_df)
            thread_earth_north_display.add(avg_df)
            thread_mag_display.add(avg_df)
            thread_dir_display.add(avg_df)

            #hread_wave_height_display.shutdown()
            #thread_earth_east_display.shutdown()
            #thread_earth_north_display.shutdown()
            #thread_mag_display.shutdown()
            #thread_dir_display.shutdown()
