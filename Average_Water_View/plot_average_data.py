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
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn


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

        self.max_points = 4096
        if int(self.rti_config.config['PLOT']['MAX_POINTS']) > 0:
            self.max_points = int(self.rti_config.config['PLOT']['MAX_POINTS'])

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

        # Callback toupdate the plot
        doc.add_periodic_callback(self.update_live_plot, callback_rate)

        doc.title = "ADCP Dashboard"

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

        # Lock the thread so not updating the data while
        # trying to update the display
        #t = time.process_time()
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

                self.cds.stream(new_data, rollover=self.max_points)
        #print("Update Plot: " + str(time.process_time() - t))

    def process_ens_group(self, fourbeam_ens, vert_ens):
        """
        Add the Ensemble group to the plot buffers.
        This will take a 4 beam ensemble and a vertical beam ensemble
        and extract the data.  It will then add the data to buffers so
        they can be plotted.

        If vert_ens is None, it means no vertical beam data is available, so use only the 4 beam data.

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

                # Check if no vertical beam exists
                if not vert_ens:
                    if fourbeam_ens.IsAncillaryData:
                        self.buffer_wave_height.append(fourbeam_ens.AncillaryData.TransducerDepth)  # Xdcr Depth
                    if fourbeam_ens.IsEnsembleData:
                        self.buffer_datetime.append(fourbeam_ens.EnsembleData.datetime())           # Datetime
                    if fourbeam_ens.IsRangeTracking:
                        self.buffer_range_track.append(fourbeam_ens.RangeTracking.avg_range())      # Range Tracking
                    # No Ancillary Pressure data but there is range tracking data, use Range Tracking
                    if not fourbeam_ens.IsAncillaryData and fourbeam_ens.IsRangeTracking:
                        self.buffer_range_track.append(fourbeam_ens.RangeTracking.avg_range())  # Range Tracking
                    # If no Range Tracking, but Ancillary Data Pressure exist, use Pressure data
                    if not fourbeam_ens.IsRangeTracking and fourbeam_ens.IsAncillaryData:
                        self.buffer_wave_height.append(fourbeam_ens.AncillaryData.TransducerDepth)  # Xdcr Depth

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

    def process_awc_group(self, fourbeam_awc, vert_awc):
        """
        Add the AverageWaterColumn data to the plot buffers.
        This will take the AverageWaterColumn object and extract the data.
        It will then add the data to buffers so they can be plotted.

        AWC
        [ss_code, ss_config, num_beams, num_bins, Beam, Instrument, Earth, Mag, Dir, Pressure, xdcr_depth, first_time, last_time, range_track]

        If vert_awc is None, it means no vertical beam data is available, so use only the 4 beam data.

        :param fourbeam_awc: Average Water Column data for 4 beam data.
        :param vert_awc: Average Water Column data for vert beam data.
        :return:
        """
        #t = time.process_time()
        with self.thread_lock:

            # Selected bins
            bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
            bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
            bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

            if vert_awc:
                # Datetime
                if vert_awc[AverageWaterColumn.INDEX_LAST_TIME]:
                    self.buffer_datetime.append(vert_awc[AverageWaterColumn.INDEX_LAST_TIME])                # Should only be 1 value

                # Xdcr Depth
                if vert_awc[AverageWaterColumn.INDEX_XDCR_DEPTH] and len(vert_awc[AverageWaterColumn.INDEX_XDCR_DEPTH]) > 0:
                    self.buffer_wave_height.append(vert_awc[AverageWaterColumn.INDEX_XDCR_DEPTH][-1])        # Should only be 1 value

                # Range Tracking
                if vert_awc[AverageWaterColumn.INDEX_RANGE_TRACK] and len(vert_awc[AverageWaterColumn.INDEX_RANGE_TRACK]) > 0:
                    self.buffer_range_track.append(vert_awc[AverageWaterColumn.INDEX_RANGE_TRACK][-1])       # Should only be 1 beam

            # 4 Beam data
            if fourbeam_awc:

                # Check if no vertical beam exist
                if not vert_awc:
                    # Datetime
                    if fourbeam_awc[AverageWaterColumn.INDEX_LAST_TIME]:
                        self.buffer_datetime.append(fourbeam_awc[AverageWaterColumn.INDEX_LAST_TIME])  # Should only be 1 value

                    # Xdcr Depth
                    if fourbeam_awc[AverageWaterColumn.INDEX_XDCR_DEPTH] and len(fourbeam_awc[AverageWaterColumn.INDEX_XDCR_DEPTH]) > 0:
                        self.buffer_wave_height.append(fourbeam_awc[AverageWaterColumn.INDEX_XDCR_DEPTH][-1])  # Should only be 1 value

                    # Range Tracking
                    if fourbeam_awc[AverageWaterColumn.INDEX_RANGE_TRACK] and len(fourbeam_awc[AverageWaterColumn.INDEX_RANGE_TRACK]) > 0:
                        self.buffer_range_track.append(fourbeam_awc[AverageWaterColumn.INDEX_RANGE_TRACK][-1])  # Should only be 1 beam

                # East Bin 1
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_1 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1]) > 0:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1][0]):        # Check for bad velocity
                        self.buffer_earth_east_1.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1][0])
                    else:
                        self.buffer_earth_east_1.append(0.0)
                else:
                    self.buffer_earth_east_1.append(0.0)

                # East Bin 2
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_2 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2]) > 0:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2][0]):        # Check for bad velocity
                        self.buffer_earth_east_2.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2][0])
                    else:
                        self.buffer_earth_east_2.append(0.0)
                else:
                    self.buffer_earth_east_2.append(0.0)

                # East Bin 3
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_3 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3]) > 0:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3][0]):        # Check for bad velocity
                        self.buffer_earth_east_3.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3][0])
                    else:
                        self.buffer_earth_east_3.append(0.0)
                else:
                    self.buffer_earth_east_3.append(0.0)

                # North Bin 1
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_1 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1]) > 1:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1][1]):        # Check for bad velocity
                        self.buffer_earth_north_1.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_1][1])
                    else:
                        self.buffer_earth_north_1.append(0.0)
                else:
                    self.buffer_earth_north_1.append(0.0)

                # North Bin 2
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_2 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2]) > 1:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2][1]):        # Check for bad velocity
                        self.buffer_earth_north_2.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_2][1])
                    else:
                        self.buffer_earth_north_2.append(0.0)
                else:
                    self.buffer_earth_north_2.append(0.0)

                # North Bin 3
                if len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH]) > bin_3 and len(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3]) > 1:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3][1]):        # Check for bad velocity
                        self.buffer_earth_north_3.append(fourbeam_awc[AverageWaterColumn.INDEX_EARTH][bin_3][1])
                    else:
                        self.buffer_earth_north_3.append(0.0)
                else:
                    self.buffer_earth_north_3.append(0.0)

                # Mag 1
                if len(fourbeam_awc[AverageWaterColumn.INDEX_MAG]) > bin_1:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_1]):            # Check for bad velocity
                        self.buffer_mag_1.append(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_1])
                    else:
                        self.buffer_mag_1.append(0.0)
                else:
                    self.buffer_mag_1.append(0.0)

                # Mag 2
                if len(fourbeam_awc[AverageWaterColumn.INDEX_MAG]) > bin_2:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_2]):
                        self.buffer_mag_2.append(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_2])
                    else:
                        self.buffer_mag_2.append(0.0)
                else:
                    self.buffer_mag_2.append(0.0)

                # Mag 3
                if len(fourbeam_awc[AverageWaterColumn.INDEX_MAG]) > bin_3:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_3]):
                        self.buffer_mag_3.append(fourbeam_awc[AverageWaterColumn.INDEX_MAG][bin_3])
                    else:
                        self.buffer_mag_3.append(0.0)
                else:
                    self.buffer_mag_3.append(0.0)

                # Dir 1
                if len(fourbeam_awc[AverageWaterColumn.INDEX_DIR]) > bin_1:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_1]):
                        self.buffer_dir_1.append(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_1])
                    else:
                        self.buffer_dir_1.append(0.0)
                else:
                    self.buffer_dir_1.append(0.0)

                # Dir 2
                if len(fourbeam_awc[AverageWaterColumn.INDEX_DIR]) > bin_2:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_2]):
                        self.buffer_dir_2.append(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_2])
                    else:
                        self.buffer_dir_2.append(0.0)
                else:
                    self.buffer_dir_2.append(0.0)

                # Dir 3
                if len(fourbeam_awc[AverageWaterColumn.INDEX_DIR]) > bin_3:
                    if not Ensemble.Ensemble.is_bad_velocity(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_3]):
                        self.buffer_dir_3.append(fourbeam_awc[AverageWaterColumn.INDEX_DIR][bin_3])
                    else:
                        self.buffer_dir_3.append(0.0)
                else:
                    self.buffer_dir_3.append(0.0)

        #print("Process AWC: " + str(time.process_time() - t))

