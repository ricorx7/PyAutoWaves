from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import time
import matplotlib.pyplot as plt
import os
import logging
from threading import Event
from collections import deque
from bokeh.io import save, output_file


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

    def plot_wave_height(self, avg_df):
        """
        Create a HTML plot of the wave height data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :return:
        """
        # Sort the data for only the "XdcrDepth" data type
        selected_avg_df = avg_df[avg_df.data_type.str.contains("XdcrDepth")]

        # Remove all the columns except datetime and value
        selected_avg_df = selected_avg_df[['datetime', 'value']]

        # Set independent variables or index
        kdims = [('datetime', 'Date and Time')]

        # Set the dependent variables or measurements
        vdims = hv.Dimension(('value', 'Wave Height'), unit='m')

        # Plot and select a bin
        plot = hv.Curve(selected_avg_df, kdims, vdims) + hv.Table(selected_avg_df)

        # Save the plot to a file
        renderer = hv.renderer('bokeh')
        bk_plot = renderer.get_plot(plot).state
        output_file(self.html_file)
        save(bk_plot)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def get_plot_earth_vel(self, avg_df, data_type, beam_num, selected_bin, label, value_label="Water Velocity", value_unit="m/s"):
        """
        Create a HTML plot of the Earth Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :param beam_num: Beam number.
        :param selected_bin: Selected bin.
        :param label: Plot label.
        :return:
        """
        # Sort the data for only the "EarthVel" data type
        # selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.bin_num == bin_num)]
        selected_avg_df = avg_df[(avg_df.data_type.str.contains(data_type))]

        # Remove all the columns except datetime and value
        # selected_avg_df = selected_avg_df[['datetime', 'bin_num', 'beam_num', 'value']]

        # Set independent variables or index
        kdims = [('datetime', 'Date'), ('bin_num', 'bin'), ('beam_num', 'beam'), 'ss_code', 'ss_config']

        # Set the dependent variables or measurements
        vdims = hv.Dimension(('value', value_label), unit=value_unit)

        # Set the independent columns
        # Create the Holoview dataset
        ds = hv.Dataset(selected_avg_df, kdims, vdims)

        bin_list = []
        bin_list.append(selected_bin)
        subset = ds.select(bin_num=bin_list, beam_num=beam_num)

        value_label_str = value_label + "(" + value_unit + ")"
        # Create the plot options
        plot = hv.Curve(subset, ('datetime', 'Date'), ('value', value_label_str), label=label)

        return plot

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
        # Title
        title = "Earth Velocity"

        east_bin_1 = self.get_plot_earth_vel(avg_df, "EarthVel", 0, selected_bin_1, 'Bin ' + str(selected_bin_1))
        east_bin_2 = self.get_plot_earth_vel(avg_df, "EarthVel", 0, selected_bin_2, 'Bin ' + str(selected_bin_2))
        east_bin_3 = self.get_plot_earth_vel(avg_df, "EarthVel", 0, selected_bin_3, 'Bin ' + str(selected_bin_3))

        #north_bin_1 = self.get_plot_earth_vel(avg_df, 1, selected_bin_1, 'North Bin ' + str(selected_bin_1))
        #north_bin_2 = self.get_plot_earth_vel(avg_df, 1, selected_bin_2, 'North Bin ' + str(selected_bin_2))
        #north_bin_3 = self.get_plot_earth_vel(avg_df, 1, selected_bin_3, 'North Bin ' + str(selected_bin_3))

        plots_east = (east_bin_1 * east_bin_2 * east_bin_3).relabel("Earth Velocity East")
        #plots_north = (north_bin_1 * north_bin_2 * north_bin_3).relabel("Earth Velocity North")
        #plots = plots_east + plots_north
        plots_east.opts(legend_position='top_left')
        #plots_north.opts(legend_position='top_left')

        # Save the plot to a file
        #hv.save(plots_east, self.html_file, fmt='html')
        renderer = hv.renderer('bokeh')
        bk_plot = renderer.get_plot(plots_east).state
        output_file(self.html_file)
        save(bk_plot)

        # Save the plot to a file
        # Include the group by
        # hv.renderer('bokeh').save(plot, self.earth_vel_html_file, fmt='scrubber')

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
        # Title
        title = "Earth Velocity East"

        north_bin_1 = self.get_plot_earth_vel(avg_df, "EarthVel", 1, selected_bin_1, 'Bin ' + str(selected_bin_1))
        north_bin_2 = self.get_plot_earth_vel(avg_df, "EarthVel", 1, selected_bin_2, 'Bin ' + str(selected_bin_2))
        north_bin_3 = self.get_plot_earth_vel(avg_df, "EarthVel", 1, selected_bin_3, 'Bin ' + str(selected_bin_3))

        plots = (north_bin_1 * north_bin_2 * north_bin_3).relabel("Earth Velocity North")
        plots.opts(legend_position='top_left')

        # Save the plot to a file
        renderer = hv.renderer('bokeh')
        bk_plot = renderer.get_plot(plots).state
        output_file(self.html_file, title="Earth Velocity North")
        save(bk_plot)

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
        # Title
        title = "Velocity Magnitude"

        bin_1 = self.get_plot_earth_vel(avg_df, "Magnitude", 0, selected_bin_1, 'Bin ' + str(selected_bin_1))
        bin_2 = self.get_plot_earth_vel(avg_df, "Magnitude", 0, selected_bin_2, 'Bin ' + str(selected_bin_2))
        bin_3 = self.get_plot_earth_vel(avg_df, "Magnitude", 0, selected_bin_3, 'Bin ' + str(selected_bin_3))

        plots = (bin_1 * bin_2 * bin_3).relabel("Velocity Magnitude")
        plots.opts(legend_position='top_left')

        # Save the plot to a file
        renderer = hv.renderer('bokeh')
        bk_plot = renderer.get_plot(plots).state
        output_file(self.html_file, title=title)
        save(bk_plot)

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
        # Title
        title = "Water Direction"

        bin_1 = self.get_plot_earth_vel(avg_df, "Direction", 0, selected_bin_1, 'Bin ' + str(selected_bin_1), "Direction", "Degrees")
        bin_2 = self.get_plot_earth_vel(avg_df, "Direction", 0, selected_bin_2, 'Bin ' + str(selected_bin_2), "Direction", "Degrees")
        bin_3 = self.get_plot_earth_vel(avg_df, "Direction", 0, selected_bin_3, 'Bin ' + str(selected_bin_3), "Direction", "Degrees")

        plots = (bin_1 * bin_2 * bin_3).relabel("Water Direction")
        plots.opts(legend_position='top_left')

        # Save the plot to a file
        renderer = hv.renderer('bokeh')
        bk_plot = renderer.get_plot(plots).state
        output_file(self.html_file, title=title)
        save(bk_plot)

        # Refresh the web view
        self.refresh_web_view_sig.emit()

    def plot_earth_vel_mpl(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        ax = plt.gca()
        avg_df.plot(kind="line", x='datetime', y='value', ax=ax)

        # plt.show()
        plt.savefig(self.earth_vel_html_file + ".png")