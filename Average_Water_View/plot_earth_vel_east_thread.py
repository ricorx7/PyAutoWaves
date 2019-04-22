from PyQt5.QtCore import QThread, pyqtSignal
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import time
import matplotlib.pyplot as plt
import os


class PlotEarthVelEastThread(QThread):
    """
    Plot the data using a QThread.
    """

    refresh_wave_height_web_view_sig = pyqtSignal()
    refresh_earth_vel_web_view_sig = pyqtSignal()

    def __init__(self, avg_df, rti_config):
        QThread.__init__(self)

        self.rti_config = rti_config
        self.avg_df = avg_df
        self.wave_height_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "WaveHeight"
        self.earth_vel_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel"

    def run(self):
        """
        Read in the CSV file.  Then plot the data.
        :return:
        """

        # Read in the CSV data of the average data
        #avg_df = pd.read_csv(self.csv_file_path)

        # Set the datetime column values as datetime values
        #avg_df['datetime'] = pd.to_datetime(avg_df['datetime'])

        # Sort the data by date and time
        #avg_df.sort_values(by=['datetime'], inplace=True)

        # Create a thread to plot the height
        #self.plot_wave_height(avg_df)

        # Update the Earth Vel Plot
        self.plot_earth_vel_east(self.avg_df,
                            int(self.rti_config.config['Waves']['selected_bin_1']),
                            int(self.rti_config.config['Waves']['selected_bin_2']),
                            int(self.rti_config.config['Waves']['selected_bin_3']))

        # Update the Earth Vel Plot
        #self.plot_earth_vel_north(avg_df,
        #                    int(self.rti_config.config['Waves']['selected_bin_1']),
        #                    int(self.rti_config.config['Waves']['selected_bin_2']),
        #                    int(self.rti_config.config['Waves']['selected_bin_3']))

        # self.plot_earth_vel_mpl(avg_df,
        #                    int(self.rti_config.config['Waves']['selected_bin_1']),
        #                    int(self.rti_config.config['Waves']['selected_bin_2']),
        #                    int(self.rti_config.config['Waves']['selected_bin_3']))

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
        hv.save(plot, self.wave_height_html_file, fmt='html')

        # Refresh the web view
        self.refresh_wave_height_web_view_sig.emit()

    def get_plot_earth_vel(self, avg_df, beam_num, selected_bin, label):
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
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel"))]

        # Remove all the columns except datetime and value
        # selected_avg_df = selected_avg_df[['datetime', 'bin_num', 'beam_num', 'value']]

        # Set independent variables or index
        kdims = [('datetime', 'Date'), ('bin_num', 'bin'), ('beam_num', 'beam'), 'ss_code', 'ss_config']

        # Set the dependent variables or measurements
        vdims = hv.Dimension(('value', 'Water Velocity'), unit='m/s')

        # Set the independent columns
        # Create the Holoview dataset
        ds = hv.Dataset(selected_avg_df, kdims, vdims)

        bin_list = []
        bin_list.append(selected_bin)
        subset = ds.select(bin_num=bin_list, beam_num=beam_num)

        # Create the plot options
        plot = hv.Curve(subset, ('datetime', 'Date'), ('value', 'Velocity (m/s)'), label=label)

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
        title = "Earth Velocity East"

        east_bin_1 = self.get_plot_earth_vel(avg_df, 0, selected_bin_1, 'East Bin ' + str(selected_bin_1))
        east_bin_2 = self.get_plot_earth_vel(avg_df, 0, selected_bin_2, 'East Bin ' + str(selected_bin_2))
        east_bin_3 = self.get_plot_earth_vel(avg_df, 0, selected_bin_3, 'East Bin ' + str(selected_bin_3))

        #north_bin_1 = self.get_plot_earth_vel(avg_df, 1, selected_bin_1, 'North Bin ' + str(selected_bin_1))
        #north_bin_2 = self.get_plot_earth_vel(avg_df, 1, selected_bin_2, 'North Bin ' + str(selected_bin_2))
        #north_bin_3 = self.get_plot_earth_vel(avg_df, 1, selected_bin_3, 'North Bin ' + str(selected_bin_3))

        plots_east = (east_bin_1 * east_bin_2 * east_bin_3).relabel("Earth Velocity East")
        #plots_north = (north_bin_1 * north_bin_2 * north_bin_3).relabel("Earth Velocity North")
        #plots = plots_east + plots_north
        plots_east.opts(legend_position='top_left')
        #plots_north.opts(legend_position='top_left')

        # Save the plot to a file
        hv.save(plots_east, self.earth_vel_html_file + "_east", fmt='html')

        # Save the plot to a file
        # Include the group by
        # hv.renderer('bokeh').save(plot, self.earth_vel_html_file, fmt='scrubber')

        # Refresh the web view
        self.refresh_earth_vel_web_view_sig.emit()

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

        north_bin_1 = self.get_plot_earth_vel(avg_df, 1, selected_bin_1, 'Bin ' + str(selected_bin_1))
        north_bin_2 = self.get_plot_earth_vel(avg_df, 1, selected_bin_2, 'Bin ' + str(selected_bin_2))
        north_bin_3 = self.get_plot_earth_vel(avg_df, 1, selected_bin_3, 'Bin ' + str(selected_bin_3))

        plots = (north_bin_1 * north_bin_2 * north_bin_3).relabel("Earth Velocity North")
        plots.opts(legend_position='top_left')

        # Save the plot to a file
        hv.save(plots, self.earth_vel_html_file + "_north", fmt='html')

        # Save the plot to a file
        # Include the group by
        # hv.renderer('bokeh').save(plot, self.earth_vel_html_file, fmt='scrubber')

        # Refresh the web view
        self.refresh_earth_vel_web_view_sig.emit()

    def plot_earth_vel_mpl(self, avg_df, selected_bin_1, selected_bin_2, selected_bin_3):
        ax = plt.gca()
        avg_df.plot(kind="line", x='datetime', y='value', ax=ax)

        # plt.show()
        plt.savefig(self.earth_vel_html_file + ".png")