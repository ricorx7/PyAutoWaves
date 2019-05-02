from bokeh.plotting import figure, output_file, show, save
from bokeh.models import LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar
from bokeh.transform import transform, linear_cmap
from bokeh.palettes import Viridis3, Viridis256, Inferno256
from bokeh.models import HoverTool
from bokeh.models import Range1d
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import panel as pn
pn.extension()
from bokeh.plotting import figure, ColumnDataSource
from collections import deque
from bokeh.layouts import row, column, gridplot, layout, grid
import numpy as np
import holoviews.plotting.bokeh


class PlotHvAverageData:

    def __init__(self, rti_config):

        self.rti_config = rti_config

        self.renderer = hv.renderer('bokeh').instance(mode='server')

        self.points = hv.Points(np.random.randn(1000, 2)).opts(tools=['box_select', 'lasso_select'])
        self.selection = hv.streams.Selection1D(source=self.points)

        self.buffer_datetime = deque()
        self.buffer_wave_height = deque()
        self.buffer_earth_east_1 = deque()
        self.buffer_earth_east_2 = deque()
        self.buffer_earth_east_3 = deque()
        self.buffer_earth_north_1 = deque()
        self.buffer_earth_north_2 = deque()
        self.buffer_earth_north_3 = deque()
        self.buffer_mag_1 = deque()
        self.buffer_mag_2 = deque()
        self.buffer_mag_3 = deque()
        self.buffer_dir_1 = deque()
        self.buffer_dir_2 = deque()
        self.buffer_dir_3 = deque()

    def create_bokeh_plots(self):
        """
        Create the bokeh plot.

        Create the ColumnDataSource to hold all the plot's data.
        Create all the plots and use the ColumnDataSource for the data.
        :return:
        """

        self.points = hv.Points(np.random.randn(1000, 2)).opts(tools=['box_select', 'lasso_select'])
        self.selection = hv.streams.Selection1D(source=self.points)

    def setup_bokeh_server(self, doc):
        """
        Setup the bokeh server in the mainwindow.py.  The server
        must be started on the main thread.

        Use the doc given to create a layout.
        Also create a callback to update the plot to
        view the live data.

        :param doc: Doc used to display the data to the webpage
        :return:
        """
        self.create_bokeh_plots()

        layout = self.points + hv.DynamicMap(self.selected_info, streams=[self.selection])

        doc = self.renderer.server_doc(layout)
        #doc.add_root(layout)
        #doc.add_root(self.renderer.app(layout))
        #doc.add_periodic_callback(self.update_live_plot, 500)
        doc.title = 'HoloViews App'

        #return self.renderer.app(layout)

        #doc = self.renderer.server_doc(layout)
        #doc.add_periodic_callback(self.update_live_plot, 500)
        #doc.title = "HoloViews App"

        #plot = self.renderer.get_plot(layout, doc=doc)
        #doc.add_root(plot)
        #doc.title = "HoloViews App"


    def selected_info(self, index):
        arr = self.points.array()[index]
        if index:
            label = 'Mean x, y: %.3f, %.3f' % tuple(arr.mean(axis=0))
        else:
            label = 'No selection'
        return self.points.clone(arr, label=label).opts(color='red')

    def update_live_plot(self):
        """
        Update the plot with live data.
        This will be called by the bokeh callback.

        Take all the data from the buffers and populate
        the ColumnDataSource.  All the lists in the ColumnDataSource
        must have the same size.

        Call Stream to update the plot.  This will append the latest data
        to the plot.
        :return:
        """

        print("update live plot hv")

    def update_dashboard(self, avg_df):
        """
        Update the dashboard plots.
        This will remove the data from the buffer and add it to the column data source for the plot.

        Dataframe columns: ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "blank", "bin_size", "value"]
        :param avg_df: Dataframe to update the plots.
        :return:
        """

        print("update_dashboard")


    def get_wave_height_list(self, avg_df, buffer_wave, buffer_dt):
        """
        Add The wave height and datetime data to the buffer.
        :param avg_df: Dataframe with the latest data.
        :param buffer_wave: Wave Height Buffer.
        :param buffer_dt: Datetime Buffer.
        :return:
        """
        # Wave Height and Datetime
        wave_height_df = avg_df[avg_df.data_type.str.contains("XdcrDepth") &
                                ((avg_df['ss_code'] == 'A') |      # vertical beam
                                (avg_df['ss_code'] == 'B') |
                                (avg_df['ss_code'] == 'C'))]
        last_row = wave_height_df.tail(1)
        if not last_row.empty:
            buffer_wave.append(last_row['value'].values[0])
            buffer_dt.append(last_row['datetime'].values[0])

    def get_earth_vel_list(self, avg_df, bin_num, beam, buffer):
        """
        Get the Earth Velocity data based off the bin and beam given.
        :param avg_df: Dataframe with earth velocity data.
        :param bin_num: Bin number to select.
        :param beam: Beam Number to select
        :param buffer: Buffer to add data to.
        :return: List of all the data found in the dataframe
        """

        earth_vel_df = avg_df.loc[(avg_df.data_type.str.contains("EarthVel")) &
                                  (avg_df['bin_num'] == bin_num) &
                                  (avg_df['beam_num'] == beam) &
                                  (avg_df['ss_code'] != 'A') &      # Not a vertical beam
                                  (avg_df['ss_code'] != 'B') &
                                  (avg_df['ss_code'] != 'C')]

        last_row = earth_vel_df.tail(1)
        if not last_row.empty:
            buffer.append(last_row['value'].values[0])

    def get_mag_list(self, avg_df, bin_num, buffer):
        """
        Get the Water Velocity data based off the bin and beam given.
        :param avg_df: Dataframe with Water Velocity data.
        :param bin_num: Bin number to select.
        :param buffer: Buffer to add data to.
        :return: List of all the data found in the dataframe
        """

        mag_df = avg_df.loc[(avg_df.data_type.str.contains("Magnitude")) &
                                  (avg_df['bin_num'] == bin_num) &
                                  (avg_df['ss_code'] != 'A') &      # Not a vertical beam
                                  (avg_df['ss_code'] != 'B') &
                                  (avg_df['ss_code'] != 'C')]

        last_row = mag_df.tail(1)
        if not last_row.empty:
            buffer.append(last_row['value'].values[0])

    def get_dir_list(self, avg_df, bin_num, buffer):
        """
        Get the Water Direction data based off the bin and beam given.
        :param avg_df: Dataframe with Water Direction data.
        :param bin_num: Bin number to select.
        :param buffer: Buffer to add data to.
        :return: List of all the data found in the dataframe
        """

        dir_df = avg_df.loc[(avg_df.data_type.str.contains("Direction")) &
                                  (avg_df['bin_num'] == bin_num) &
                                  (avg_df['ss_code'] != 'A') &      # Not a vertical beam
                                  (avg_df['ss_code'] != 'B') &
                                  (avg_df['ss_code'] != 'C')]

        last_row = dir_df.tail(1)
        if not last_row.empty:
            buffer.append(last_row['value'].values[0])
