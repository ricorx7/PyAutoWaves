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
import time
from threading import Lock, Thread
from rti_python.Ensemble import Ensemble


class PlotAverageData:
    """
    The data will be averaged and saved to a CSV file.  This
    will also plot the averaged data live to a web browser.
    """

    def __init__(self, rti_config):

        self.rti_config = rti_config

        self.cds = ColumnDataSource(data=dict(date=[],
                                              wave_height=[],
                                              earth_east_1=[],
                                              earth_east_2=[],
                                              earth_east_3=[],
                                              earth_north_1=[],
                                              earth_north_2=[],
                                              earth_north_3=[],
                                              mag_1=[],
                                              mag_2=[],
                                              mag_3=[],
                                              dir_1=[],
                                              dir_2=[],
                                              dir_3=[]))

        self.buffer_datetime = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_wave_height = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_range_track = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_east_1 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_east_2 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_east_3 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_north_1 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_north_2 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_earth_north_3 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_mag_1 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_mag_2 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_mag_3 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_dir_1 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_dir_2 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_dir_3 = deque(maxlen=int(self.rti_config.config['PLOT']['BUFF_SIZE']))
        self.buffer_dash_df = deque(maxlen=int(self.rti_config.config['Waves']['ENS_IN_BURST'])*2)
        self.buffer_dash_ens = deque(maxlen=int(self.rti_config.config['Waves']['ENS_IN_BURST']) * 2)
        self.thread_lock = Lock()
        self.csv_file_path = ""

    def set_csv_file_path(self, file_path):
        self.csv_file_path = file_path

    def create_bokeh_plots(self):
        """
        Create the bokeh plot.

        Create the ColumnDataSource to hold all the plot's data.
        Create all the plots and use the ColumnDataSource for the data.
        :return:
        """
        self.cds = ColumnDataSource(data=dict(date=[],
                                              wave_height=[],
                                              range_track=[],
                                              earth_east_1=[],
                                              earth_east_2=[],
                                              earth_east_3=[],
                                              earth_north_1=[],
                                              earth_north_2=[],
                                              earth_north_3=[],
                                              mag_1=[],
                                              mag_2=[],
                                              mag_3=[],
                                              dir_1=[],
                                              dir_2=[],
                                              dir_3=[]))

        # Specify the selection tools to be made available
        select_tools = ['box_select', 'lasso_select', 'poly_select', 'tap', 'reset', 'previewsave', 'pan', 'wheel_zoom', 'box_zoom', 'hover']

        # Format the tooltip
        tooltips_wave_height = HoverTool(tooltips=[
            ('Date-Time', '@date{%F %H:%M:%S}'),
            ('Pressure Height (m)', '@wave_height'),
            ('Range Tracking Height (m)', '@range_track'),
        ], formatters={'date': 'datetime'})

        # Format the tooltip
        tooltips_vel_east = HoverTool(tooltips=[
            ('Time', '@date{%F %T}'),
            ('Velocity (m/s) Bin 1', '@earth_east_1'),
            ('Velocity (m/s) Bin 2', '@earth_east_2'),
            ('Velocity (m/s) Bin 3', '@earth_east_3'),
        ], formatters={'date': 'datetime'})

        # Format the tooltip
        tooltips_vel_north = HoverTool(tooltips=[
            ('Time', '@date{%F %T}'),
            ('Velocity (m/s) Bin 1', '@earth_north_1'),
            ('Velocity (m/s) Bin 2', '@earth_north_2'),
            ('Velocity (m/s) Bin 3', '@earth_north_3'),
        ], formatters={'date': 'datetime'})

        # Format the tooltip
        tooltips_mag = HoverTool(tooltips=[
            ('Time', '@date{%F %T}'),
            ('Velocity (m/s) Bin 1', '@mag_1'),
            ('Velocity (m/s) Bin 2', '@mag_2'),
            ('Velocity (m/s) Bin 3', '@mag_3'),
        ], formatters={'date': 'datetime'})

        # Format the tooltip
        tooltips_dir = HoverTool(tooltips=[
            ('Time', '@date{%F %T}'),
            ('Velocity (deg) Bin 1', '@dir_1'),
            ('Velocity (deg) Bin 2', '@dir_2'),
            ('Velocity (deg) Bin 3', '@dir_3'),
        ], formatters={'date': 'datetime'})

        max_display = 200

        self.plot_range = figure(x_axis_type='datetime', title="Wave Height")
        self.plot_range.x_range.follow_interval = max_display
        self.plot_range.xaxis.axis_label = "Time"
        self.plot_range.yaxis.axis_label = "Wave Height (m)"
        self.plot_range.add_tools(tooltips_wave_height)
        self.line_wave_height = self.plot_range.line(x='date', y='wave_height', line_width=2, legend="Pressure", source=self.cds, color='navy', name="wave_height")
        self.line_range_track = self.plot_range.line(x='date', y='range_track', line_width=2, legend="Range Track", source=self.cds, color='orange', name="range track")

        legend_bin_1 = "Bin" + self.rti_config.config['Waves']['selected_bin_1']
        legend_bin_2 = "Bin" + self.rti_config.config['Waves']['selected_bin_2']
        legend_bin_3 = "Bin" + self.rti_config.config['Waves']['selected_bin_3']

        self.plot_earth_east = figure(x_axis_type='datetime', title="Earth Velocity East")
        self.plot_earth_east.x_range.follow_interval = max_display
        self.plot_earth_east.xaxis.axis_label = "Time"
        self.plot_earth_east.yaxis.axis_label = "Velocity (m/s)"
        self.plot_earth_east.add_tools(tooltips_vel_east)
        self.line_east_1 = self.plot_earth_east.line(x='date', y='earth_east_1', line_width=2, source=self.cds, legend=legend_bin_1, color='navy', name="east_1")
        self.line_east_2 = self.plot_earth_east.line(x='date', y='earth_east_2', line_width=2, source=self.cds, legend=legend_bin_2, color='skyblue', name="east_2")
        self.line_east_3 = self.plot_earth_east.line(x='date', y='earth_east_3', line_width=2, source=self.cds, legend=legend_bin_3, color='orange', name="east_3")

        self.plot_earth_north = figure(x_axis_type='datetime', title="Earth Velocity North")
        self.plot_earth_north.x_range.follow_interval = max_display
        self.plot_earth_north.xaxis.axis_label = "Time"
        self.plot_earth_north.yaxis.axis_label = "Velocity (m/s)"
        self.plot_earth_north.add_tools(tooltips_vel_north)
        self.line_north_1 = self.plot_earth_north.line(x='date', y='earth_north_1', line_width=2, source=self.cds, legend=legend_bin_1, color='navy', name="north_1")
        self.line_north_2 = self.plot_earth_north.line(x='date', y='earth_north_2', line_width=2, source=self.cds, legend=legend_bin_2, color='skyblue', name="north_2")
        self.line_north_3 = self.plot_earth_north.line(x='date', y='earth_north_3', line_width=2, source=self.cds, legend=legend_bin_3, color='orange', name="north_3")

        self.plot_mag = figure(x_axis_type='datetime', title="Water Velocity")
        self.plot_mag.x_range.follow_interval = max_display
        self.plot_mag.xaxis.axis_label = "Time"
        self.plot_mag.yaxis.axis_label = "Velocity (m/s)"
        self.plot_mag.add_tools(tooltips_mag)
        self.line_mag_1 = self.plot_mag.line(x='date', y='mag_1', line_width=2, source=self.cds, legend=legend_bin_1, color='navy', name="mag_1")
        self.line_mag_2 = self.plot_mag.line(x='date', y='mag_2', line_width=2, source=self.cds, legend=legend_bin_2, color='skyblue', name="mag_2")
        self.line_mag_3 = self.plot_mag.line(x='date', y='mag_3', line_width=2, source=self.cds, legend=legend_bin_3, color='orange', name="mag_3")

        self.plot_dir = figure(x_axis_type='datetime', title="Water Direction")
        self.plot_dir.x_range.follow_interval = max_display
        self.plot_dir.xaxis.axis_label = "Time"
        self.plot_dir.yaxis.axis_label = "Direction (degrees)"
        self.plot_dir.add_tools(tooltips_dir)
        self.line_dir_1 = self.plot_dir.line(x='date', y='dir_1', line_width=2, source=self.cds,
                                                     legend=legend_bin_1, color='navy', name="dir_1")
        self.line_dir_2 = self.plot_dir.line(x='date', y='dir_2', line_width=2, source=self.cds,
                                                     legend=legend_bin_2, color='skyblue', name="dir_2")
        self.line_dir_3 = self.plot_dir.line(x='date', y='dir_3', line_width=2, source=self.cds,
                                                     legend=legend_bin_3, color='orange', name="dir_3")

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

        plot_layout = layout([
            [self.plot_range],
            [self.plot_earth_east, self.plot_earth_north],
            [self.plot_mag, self.plot_dir]
        ], sizing_mode='stretch_both')

        #plot_layout = grid([self.plot_range, None, self.plot_earth_east, self.plot_earth_north], ncols=2)

        callback_rate = 2500
        if int(self.rti_config.config['PLOT']['RATE']) > 1000:
            callback_rate = int(self.rti_config.config['PLOT']['RATE'])

        doc.add_root(plot_layout)

        # Determine which callback function to used based off averaging is turned on or off
        # If averaging is turned on, use the df buffered data
        # If averaging is turned off, use the ens buffered data
        if int(self.rti_config.config['AWC']['num_ensembles']) > 1:
            doc.add_periodic_callback(self.update_live_plot_df, callback_rate)
        else:
            doc.add_periodic_callback(self.update_live_plot_ens, callback_rate)

        doc.title = "ADCP Dashboard"

    def update_live_plot_df(self):
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

        # Lock the thread so not updating the data while
        # trying to update the display
        t = time.process_time()
        with self.thread_lock:

            # Load all the data from the buffer
            # Each dataframe takes about 2 second to process
            # Limit the number of df to process to ensure there is
            # enough time to display before the next plot update
            for x in range(min(round(len(self.buffer_dash_df)), 50)):
                if self.buffer_dash_df:
                    self.process_dashboard_buffer(self.buffer_dash_df.popleft())

            print("Ens Buff Size: " + str(len(self.buffer_dash_df)))

            # Verify that a least one complete dataset has been received
            if len(self.buffer_datetime) > 0 and len(self.buffer_wave_height) > 0 and len(self.buffer_earth_east_1) > 0 and len(self.buffer_earth_east_2) > 0 and len(self.buffer_earth_east_3) > 0 and len(self.buffer_earth_north_1) > 0 and len(self.buffer_earth_north_2) > 0 and len(self.buffer_earth_north_3) > 0 and len(self.buffer_mag_1) > 0 and len(self.buffer_mag_2) > 0 and len(self.buffer_mag_3) > 0 and len(self.buffer_dir_1) > 0 and len(self.buffer_dir_2) > 0 and len(self.buffer_dir_3) > 0:

                date_list = []
                wave_height_list = []
                range_track_list = []
                earth_east_1 = []
                earth_east_2 = []
                earth_east_3 = []
                earth_north_1 = []
                earth_north_2 = []
                earth_north_3 = []
                mag_1 = []
                mag_2 = []
                mag_3 = []
                dir_1 = []
                dir_2 = []
                dir_3 = []

                while self.buffer_datetime:
                    date_list.append(self.buffer_datetime.popleft())
                while self.buffer_wave_height:
                    wave_height_list.append(self.buffer_wave_height.popleft())
                while self.buffer_range_track:
                    range_track_list.append(self.buffer_range_track.popleft())
                while self.buffer_earth_east_1:
                    earth_east_1.append(self.buffer_earth_east_1.popleft())
                while self.buffer_earth_east_2:
                    earth_east_2.append(self.buffer_earth_east_2.popleft())
                while self.buffer_earth_east_3:
                    earth_east_3.append(self.buffer_earth_east_3.popleft())
                while self.buffer_earth_north_1:
                    earth_north_1.append(self.buffer_earth_north_1.popleft())
                while self.buffer_earth_north_2:
                    earth_north_2.append(self.buffer_earth_north_2.popleft())
                while self.buffer_earth_north_3:
                    earth_north_3.append(self.buffer_earth_north_3.popleft())
                while self.buffer_mag_1:
                    mag_1.append(self.buffer_mag_1.popleft())
                while self.buffer_mag_2:
                    mag_2.append(self.buffer_mag_2.popleft())
                while self.buffer_mag_3:
                    mag_3.append(self.buffer_mag_3.popleft())
                while self.buffer_dir_1:
                    dir_1.append(self.buffer_dir_1.popleft())
                while self.buffer_dir_2:
                    dir_2.append(self.buffer_dir_2.popleft())
                while self.buffer_dir_3:
                    dir_3.append(self.buffer_dir_3.popleft())

                new_data = {'date': date_list,
                            'wave_height': wave_height_list,
                            'range_track': range_track_list,
                            'earth_east_1': earth_east_1,
                            'earth_east_2': earth_east_2,
                            'earth_east_3': earth_east_3,
                            'earth_north_1': earth_north_1,
                            'earth_north_2': earth_north_2,
                            'earth_north_3': earth_north_3,
                            'mag_1': mag_1,
                            'mag_2': mag_2,
                            'mag_3': mag_3,
                            'dir_1': dir_1,
                            'dir_2': dir_2,
                            'dir_3': dir_3}

                self.cds.stream(new_data)
        print("Update Plot: " + str(time.process_time() - t))

    def update_live_plot_from_csv(self):
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

        # Lock the thread so not updating the data while
        # trying to update the display
        t = time.process_time()
        with self.thread_lock:

            date_list = []
            wave_height_list = []
            earth_east_1 = []
            earth_east_2 = []
            earth_east_3 = []
            earth_north_1 = []
            earth_north_2 = []
            earth_north_3 = []
            mag_1 = []
            mag_2 = []
            mag_3 = []
            dir_1 = []
            dir_2 = []
            dir_3 = []

            # Verify file path is not empty
            if self.csv_file_path != "":

                # Get the data from the CSV file as a dataframe
                avg_df = pd.read_csv(self.csv_file_path)

                if len(avg_df) > 0:

                    # Wave Height and Datetime
                    self.get_wave_height_list(avg_df, wave_height_list, date_list)

                    # Selected bins
                    bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
                    bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
                    bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

                    #  Update buffers
                    self.get_earth_vel_list(avg_df, bin_1, 0, earth_east_1)
                    self.get_earth_vel_list(avg_df, bin_2, 0, earth_east_2)
                    self.get_earth_vel_list(avg_df, bin_3, 0, earth_east_3)
                    self.get_earth_vel_list(avg_df, bin_1, 1, earth_north_1)
                    self.get_earth_vel_list(avg_df, bin_2, 1, earth_north_2)
                    self.get_earth_vel_list(avg_df, bin_3, 1, earth_north_3)
                    self.get_mag_list(avg_df, bin_1, mag_1)
                    self.get_mag_list(avg_df, bin_2, mag_2)
                    self.get_mag_list(avg_df, bin_3, mag_3)
                    self.get_dir_list(avg_df, bin_1, dir_1)
                    self.get_dir_list(avg_df, bin_2, dir_2)
                    self.get_dir_list(avg_df, bin_3, dir_3)

                    print("ee1 " + str(len(earth_east_1)))
                    print("ee2 " + str(len(earth_east_2)))
                    print("ee3 " + str(len(earth_east_3)))
                    print("en1 " + str(len(earth_north_1)))
                    print("en2 " + str(len(earth_north_2)))
                    print("en3 " + str(len(earth_north_3)))
                    print("mag1 " + str(len(mag_1)))
                    print("mag2 " + str(len(mag_2)))
                    print("mag3 " + str(len(mag_3)))
                    print("dir1 " + str(len(dir_1)))
                    print("dir2 " + str(len(dir_2)))
                    print("dir3 " + str(len(dir_3)))

                    if len(date_list) > 0 and len(wave_height_list) > 0 and len(earth_east_1) > 0 and len(earth_east_2) > 0 and len(earth_east_3) > 0 and len(earth_north_1) > 0 and len(earth_north_2) > 0 and len(earth_north_3) > 0 and len(mag_1) > 0 and len(mag_2) > 0 and len(mag_3) > 0 and len(dir_1) > 0 and len(dir_2) > 0 and len(dir_3) > 0:

                        new_data = {'date': date_list,
                                    'wave_height': wave_height_list,
                                    'earth_east_1': earth_east_1,
                                    'earth_east_2': earth_east_2,
                                    'earth_east_3': earth_east_3,
                                    'earth_north_1': earth_north_1,
                                    'earth_north_2': earth_north_2,
                                    'earth_north_3': earth_north_3,
                                    'mag_1': mag_1,
                                    'mag_2': mag_2,
                                    'mag_3': mag_3,
                                    'dir_1': dir_1,
                                    'dir_2': dir_2,
                                    'dir_3': dir_3}

                        self.cds.stream(new_data)
        print("Update Plot from CSV: " + str(time.process_time() - t))

    def update_live_plot_ens(self):
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

        # Lock the thread so not updating the data while
        # trying to update the display
        t = time.process_time()
        with self.thread_lock:

            # Verify that a least one complete dataset has been received
            if len(self.buffer_datetime) > 0 and len(self.buffer_wave_height) > 0 and len(self.buffer_range_track) > 0 and len(self.buffer_earth_east_1) > 0 and len(self.buffer_earth_east_2) > 0 and len(self.buffer_earth_east_3) > 0 and len(self.buffer_earth_north_1) > 0 and len(self.buffer_earth_north_2) > 0 and len(self.buffer_earth_north_3) > 0 and len(self.buffer_mag_1) > 0 and len(self.buffer_mag_2) > 0 and len(self.buffer_mag_3) > 0 and len(self.buffer_dir_1) > 0 and len(self.buffer_dir_2) > 0 and len(self.buffer_dir_3) > 0:

                date_list = []
                wave_height_list = []
                range_track_list = []
                earth_east_1 = []
                earth_east_2 = []
                earth_east_3 = []
                earth_north_1 = []
                earth_north_2 = []
                earth_north_3 = []
                mag_1 = []
                mag_2 = []
                mag_3 = []
                dir_1 = []
                dir_2 = []
                dir_3 = []

                while self.buffer_datetime:
                    date_list.append(self.buffer_datetime.popleft())
                while self.buffer_wave_height:
                    wave_height_list.append(self.buffer_wave_height.popleft())
                while self.buffer_range_track:
                    range_track_list.append(self.buffer_range_track.popleft())
                while self.buffer_earth_east_1:
                    earth_east_1.append(self.buffer_earth_east_1.popleft())
                while self.buffer_earth_east_2:
                    earth_east_2.append(self.buffer_earth_east_2.popleft())
                while self.buffer_earth_east_3:
                    earth_east_3.append(self.buffer_earth_east_3.popleft())
                while self.buffer_earth_north_1:
                    earth_north_1.append(self.buffer_earth_north_1.popleft())
                while self.buffer_earth_north_2:
                    earth_north_2.append(self.buffer_earth_north_2.popleft())
                while self.buffer_earth_north_3:
                    earth_north_3.append(self.buffer_earth_north_3.popleft())
                while self.buffer_mag_1:
                    mag_1.append(self.buffer_mag_1.popleft())
                while self.buffer_mag_2:
                    mag_2.append(self.buffer_mag_2.popleft())
                while self.buffer_mag_3:
                    mag_3.append(self.buffer_mag_3.popleft())
                while self.buffer_dir_1:
                    dir_1.append(self.buffer_dir_1.popleft())
                while self.buffer_dir_2:
                    dir_2.append(self.buffer_dir_2.popleft())
                while self.buffer_dir_3:
                    dir_3.append(self.buffer_dir_3.popleft())

                new_data = {'date': date_list,
                            'wave_height': wave_height_list,
                            'range_track': range_track_list,
                            'earth_east_1': earth_east_1,
                            'earth_east_2': earth_east_2,
                            'earth_east_3': earth_east_3,
                            'earth_north_1': earth_north_1,
                            'earth_north_2': earth_north_2,
                            'earth_north_3': earth_north_3,
                            'mag_1': mag_1,
                            'mag_2': mag_2,
                            'mag_3': mag_3,
                            'dir_1': dir_1,
                            'dir_2': dir_2,
                            'dir_3': dir_3}

                self.cds.stream(new_data)
        print("Update Plot: " + str(time.process_time() - t))

    def update_dashboard(self, avg_df):
        """
        Buffer up the df.  They will be processed when the
        display update callback function is called.
        :param avg_df:
        :return:
        """
        with self.thread_lock:
            # Buffer up the data
            self.buffer_dash_df.append(avg_df)

    def process_ens_group(self, fourbeam_ens, vert_ens):
        """
        Add the Ensemble group to the plot buffers.
        This will take a 4 beam ensemble and a vertical beam ensemble
        and extract the data.  It will then add the data to buffers so
        they can be plotted.
        :param fourbeam_ens: 4 or 3 Beam ensemble.
        :param vert_ens:  Vertical ensemble.
        :return:
        """
        #t = time.process_time()
        with self.thread_lock:

            # Selected bins
            bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
            bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
            bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

            # Vertical beam data
            if vert_ens:
                if vert_ens.IsAncillaryData:
                    self.buffer_wave_height.append(vert_ens.AncillaryData.TransducerDepth)  # Xdcr Depth
                if vert_ens.IsEnsembleData:
                    self.buffer_datetime.append(vert_ens.EnsembleData.datetime())           # Datetime
                if vert_ens.IsRangeTracking:
                    self.buffer_range_track.append(vert_ens.RangeTracking.avg_range())      # Range Tracking

            # 4 Beam data
            if fourbeam_ens:
                if fourbeam_ens.IsEarthVelocity:
                    # East Bin 1
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_1][0]):
                        self.buffer_earth_east_1.append(fourbeam_ens.EarthVelocity.Velocities[bin_1][0])
                    else:
                        self.buffer_earth_east_1.append(0.0)

                    # East Bin 2
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_2][0]):
                        self.buffer_earth_east_2.append(fourbeam_ens.EarthVelocity.Velocities[bin_2][0])
                    else:
                        self.buffer_earth_east_2.append(0.0)

                    # East Bin 3
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_3][0]):
                        self.buffer_earth_east_3.append(fourbeam_ens.EarthVelocity.Velocities[bin_3][0])
                    else:
                        self.buffer_earth_east_3.append(0.0)

                    # North Bin 1
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_1][1]):
                        self.buffer_earth_north_1.append(fourbeam_ens.EarthVelocity.Velocities[bin_1][1])
                    else:
                        self.buffer_earth_north_1.append(0.0)

                    # North Bin 2
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_2][1]):
                        self.buffer_earth_north_2.append(fourbeam_ens.EarthVelocity.Velocities[bin_2][1])
                    else:
                        self.buffer_earth_north_2.append(0.0)

                    # North Bin 3
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Velocities[bin_3][1]):
                        self.buffer_earth_north_3.append(fourbeam_ens.EarthVelocity.Velocities[bin_3][1])
                    else:
                        self.buffer_earth_north_3.append(0.0)

                    # Mag 1
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Magnitude[bin_1]):
                        self.buffer_mag_1.append(fourbeam_ens.EarthVelocity.Magnitude[bin_1])
                    else:
                        self.buffer_mag_1.append(0.0)

                    # Mag 2
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Magnitude[bin_2]):
                        self.buffer_mag_2.append(fourbeam_ens.EarthVelocity.Magnitude[bin_2])
                    else:
                        self.buffer_mag_2.append(0.0)

                    # Mag 3
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Magnitude[bin_3]):
                        self.buffer_mag_3.append(fourbeam_ens.EarthVelocity.Magnitude[bin_3])
                    else:
                        self.buffer_mag_3.append(0.0)

                    # Dir 1
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Direction[bin_1]):
                        self.buffer_dir_1.append(fourbeam_ens.EarthVelocity.Direction[bin_1])
                    else:
                        self.buffer_dir_1.append(0.0)

                    # Dir 2
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Direction[bin_2]):
                        self.buffer_dir_2.append(fourbeam_ens.EarthVelocity.Direction[bin_2])
                    else:
                        self.buffer_dir_2.append(0.0)

                    # Dir 3
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_ens.EarthVelocity.Direction[bin_3]):
                        self.buffer_dir_3.append(fourbeam_ens.EarthVelocity.Direction[bin_3])
                    else:
                        self.buffer_dir_3.append(0.0)

        #print("Process ENS: " + str(time.process_time() - t))

    def process_dashboard_buffer(self, avg_df):
        """
        Update the dashboard plots.
        This will remove the data from the buffer and add it to the column data source for the plot.

        Dataframe columns: ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "blank", "bin_size", "value"]
        :param avg_df: Dataframe to update the plots.
        :return:
        """

        # Lock the thread while trying to update the data
        # while trying to update the display
        t = time.process_time()

        # Wave Height and Datetime
        self.get_wave_height_list(avg_df, self.buffer_wave_height, self.buffer_datetime)

        # Range Tracking
        self.get_range_track_list(avg_df, self.buffer_range_track)

        # Selected bins
        bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
        bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
        bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

        #  Update buffers
        self.get_earth_vel_list(avg_df, bin_1, 0, self.buffer_earth_east_1)
        self.get_earth_vel_list(avg_df, bin_2, 0, self.buffer_earth_east_2)
        self.get_earth_vel_list(avg_df, bin_3, 0, self.buffer_earth_east_3)
        self.get_earth_vel_list(avg_df, bin_1, 1, self.buffer_earth_north_1)
        self.get_earth_vel_list(avg_df, bin_2, 1, self.buffer_earth_north_2)
        self.get_earth_vel_list(avg_df, bin_3, 1, self.buffer_earth_north_3)
        self.get_mag_list(avg_df, bin_1, self.buffer_mag_1)
        self.get_mag_list(avg_df, bin_2, self.buffer_mag_2)
        self.get_mag_list(avg_df, bin_3, self.buffer_mag_3)
        self.get_dir_list(avg_df, bin_1, self.buffer_dir_1)
        self.get_dir_list(avg_df, bin_2, self.buffer_dir_2)
        self.get_dir_list(avg_df, bin_3, self.buffer_dir_3)

        print("Update Dashboard: " + str(time.process_time() - t) + " " + str(avg_df.shape))

    def get_wave_height_list(self, avg_df, buffer_wave, buffer_dt):
        """
        Add The wave height and datetime data to the buffer.
        :param avg_df: Dataframe with the latest data.
        :param buffer_wave: Wave Height Buffer.
        :param buffer_dt: Datetime Buffer.
        :return:
        """
        # Wave Height and Datetime
        # & avg_df.ss_code.isin(vert_filter_list)]
        wave_height_df = avg_df[(avg_df.data_type.str.contains("XdcrDepth")) &
                       ((avg_df.ss_code.str.contains("A")) |
                        (avg_df.ss_code.str.contains("B")) |
                        (avg_df.ss_code.str.contains("C")))]

        last_row = wave_height_df.tail(1)
        if not last_row.empty:
            buffer_wave.append(last_row['value'].values[0])
            buffer_dt.append(last_row['datetime'].values[0])

    def get_range_track_list(self, avg_df, buffer_range_track,):
        """
        Add The vertical beam range tracking data to the buffer.
        :param avg_df: Dataframe with the latest data.
        :param buffer_range_track: Wave Height Buffer.
        :return:
        """
        # Wave Height and Datetime
        # & avg_df.ss_code.isin(vert_filter_list)]
        range_track_df = avg_df[(avg_df.data_type.str.contains("RT_Range")) &
                       ((avg_df.ss_code.str.contains("A")) |
                        (avg_df.ss_code.str.contains("B")) |
                        (avg_df.ss_code.str.contains("C"))) &
                        (avg_df.beam_num == 0)]

        last_row = range_track_df.tail(1)
        if not last_row.empty:
            buffer_range_track.append(last_row['value'].values[0])

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

        dir_df = avg_df[(avg_df.data_type.str.contains("Direction")) &
                                  (avg_df['bin_num'] == bin_num) &
                                  (avg_df['ss_code'] != 'A') &      # Not a vertical beam
                                  (avg_df['ss_code'] != 'B') &
                                  (avg_df['ss_code'] != 'C')]

        last_row = dir_df.tail(1)
        if not last_row.empty:
            buffer.append(last_row['value'].values[0])
