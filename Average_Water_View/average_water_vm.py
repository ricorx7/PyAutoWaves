from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QUrl, QEventLoop
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import QtGui, QtWidgets, QtCore
from bokeh.plotting import figure, output_file, show, save
from bokeh.models import LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar
from bokeh.transform import transform, linear_cmap
from bokeh.palettes import Viridis3, Viridis256, Inferno256
from bokeh.models import HoverTool
from bokeh.models import Range1d
#import holoviews as hv
import streamz
from streamz.dataframe import DataFrames
import asyncio
from .average_water_thread import AverageWaterThread
from holoviews import opts
from holoviews.streams import Pipe, Buffer
import math
import pandas as pd
import numpy as np
from threading import Thread
import threading
import csv
import datetime
import queue
import collections
from . import average_water_view
import logging
from obsub import event
import os
import time
from rti_python.Utilities.config import RtiConfig
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn
from tornado.ioloop import IOLoop
from bokeh.server.server import Server
# pyviz
import numpy as np
import scipy.stats as ss
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import panel as pn
pn.extension()
from bokeh.plotting import figure, ColumnDataSource
from collections import deque
from bokeh.layouts import row, column, gridplot, layout, grid

opts.defaults(
    opts.Bars(xrotation=45, tools=['hover']),
    opts.BoxWhisker(width=800, xrotation=30, box_fill_color=Palette('Category20')),
    opts.Curve(width=600, tools=['hover']),
    opts.GridSpace(shared_yaxis=True),
    opts.Scatter(width=800, height=400, color=Palette('Category20'), size=dim('growth')+5, tools=['hover']),
    opts.NdOverlay(legend_position='left'))


class AverageWaterVM(average_water_view.Ui_AvgWater, QWidget):

    #add_ens_sig = pyqtSignal(object)
    add_tab_sig = pyqtSignal(str, object)
    populate_table_sig = pyqtSignal(str, object)
    increment_ens_sig = pyqtSignal(int)
    reset_avg_sig = pyqtSignal()
    avg_taken_sig = pyqtSignal()
    refresh_wave_height_web_view_sig = pyqtSignal()
    refresh_earth_vel_web_view_sig = pyqtSignal()

    def __init__(self, parent, rti_config):
        average_water_view.Ui_AvgWater.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.rti_config = rti_config
        self.rti_config.init_average_waves_config()

        self.average_thread = AverageWaterThread(self.rti_config)
        self.average_thread.setObjectName("Average Water Column Thread")
        self.average_thread.increment_ens_sig.connect(self.increment_ens)
        self.average_thread.avg_taken_sig.connect(self.avg_taken)
        self.average_thread.refresh_wave_height_web_view_sig.connect(self.refresh_wave_height_web_view)
        self.average_thread.refresh_earth_east_vel_web_view_sig.connect(self.refresh_earth_east_vel_web_view)
        self.average_thread.refresh_earth_north_vel_web_view_sig.connect(self.refresh_earth_north_vel_web_view)
        self.average_thread.refresh_mag_web_view_sig.connect(self.refresh_mag_web_view)
        self.average_thread.refresh_dir_web_view_sig.connect(self.refresh_dir_web_view)
        self.average_thread.start()

        self.wave_height_html_file = self.average_thread.wave_height_html_file
        self.earth_east_vel_html_file = self.average_thread.earth_east_vel_html_file
        self.earth_north_vel_html_file = self.average_thread.earth_north_vel_html_file
        self.mag_html_file = self.average_thread.mag_html_file
        self.dir_html_file = self.average_thread.dir_html_file

        # Web Views
        self.web_view_wave_height = QWebEngineView()
        self.web_view_earth_east_vel = QWebEngineView()
        self.web_view_earth_north_vel = QWebEngineView()
        self.web_view_mag = QWebEngineView()
        self.web_view_dir = QWebEngineView()

        # Latest Average Water Column
        self.avg_counter = 0

        #self.html = None
        #self.web_view = QWebEngineView()
        #html_path = os.path.split(os.path.abspath(__file__))[0] + os.sep + ".." + os.sep + self.HTML_FILE_NAME
        #html_path = self.wave_height_html_file + ".html"
        #print(html_path)
        #self.web_view.load(QUrl().fromLocalFile(html_path))

        #self.earth_vel_east_stream = ColumnDataSource({'x': [], 'y': []})

        # Initialize the dataframe
        #columns = ['datetime', 'voltage']
        #columns = ['voltage']
        #self.earth_df = pd.DataFrame(columns=columns)
        #self.earth_df['datetime'] = pd.to_datetime(self.earth_df['datetime'])

        # Create a stream for the data
        #self.earth_vel_east_stream = hv.streams.Buffer(df)
        #stream = streamz.Stream()
        #self.pipe = Pipe(data=self.earth_df)
        #self.stream = streamz.dataframe.DataFrame(stream, example=self.earth_df)
        #self.buffer = Buffer(self.stream.voltage, index=False)
        #self.dfstream = Buffer(self.earth_df)

        self.cds = ColumnDataSource(data=dict(date=[],
                                              wave_height=[],
                                              earth_east_1=[],
                                              earth_east_2=[],
                                              earth_east_3=[],
                                              earth_north_1=[],
                                              earth_north_2=[],
                                              earth_north_3=[]))
        self.buffer_voltage = deque()
        self.buffer_datetime = deque()
        self.buffer_heading = deque()
        self.buffer_wave_height = deque()
        self.buffer_earth_east_1 = deque()
        self.buffer_earth_east_2 = deque()
        self.buffer_earth_east_3 = deque()
        self.buffer_earth_north_1 = deque()
        self.buffer_earth_north_2 = deque()
        self.buffer_earth_north_3 = deque()

        #self.add_tab("Wave Height")

        self.setWindowTitle("Average Water Column")

        self.web_view_wave_height.load(QUrl().fromLocalFile(self.wave_height_html_file))
        #self.add_tab_sig.emit("Wave Height", self.web_view_wave_height)

        self.web_view_earth_east_vel.load(QUrl().fromLocalFile(self.earth_east_vel_html_file))
        #self.add_tab_sig.emit("Earth Velocity", self.web_view_earth_east_vel)

        self.web_view_earth_north_vel.load(QUrl().fromLocalFile(self.earth_north_vel_html_file))
        #self.add_tab_sig.emit("Earth Velocity", self.web_view_earth_north_vel)

        self.web_view_mag.load(QUrl().fromLocalFile(self.mag_html_file))
        self.web_view_dir.load(QUrl().fromLocalFile(self.dir_html_file))

        self.docked_wave_height = QtWidgets.QDockWidget("Wave Height", self)
        self.docked_wave_height.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_wave_height.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_wave_height.resize(1100, 380)
        self.docked_wave_height.setWidget(self.web_view_wave_height)
        self.docked_wave_height.setVisible(True)
        #self.addDockWidget(QtCore.Qt.AllDockWidgetAreas, self.docked_wave_height)

        self.docked_earth_vel_east = QtWidgets.QDockWidget("Earth Velocity - East", self)
        self.docked_earth_vel_east.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_earth_vel_east.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_earth_vel_east.resize(650, 340)
        self.docked_earth_vel_east.setWidget(self.web_view_earth_east_vel)
        self.docked_earth_vel_east.setVisible(True)
        #self.addDockWidget(QtCore.Qt.AllDockWidgetAreas, self.docked_wave_height)

        self.docked_earth_vel_north = QtWidgets.QDockWidget("Earth Velocity - North", self)
        self.docked_earth_vel_north.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_earth_vel_north.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_earth_vel_north.resize(650, 340)
        self.docked_earth_vel_north.setWidget(self.web_view_earth_north_vel)
        self.docked_earth_vel_north.setVisible(True)

        self.docked_mag = QtWidgets.QDockWidget("Velocity Magnitude", self)
        self.docked_mag.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_mag.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_mag.resize(650, 340)
        self.docked_mag.setWidget(self.web_view_mag)
        self.docked_mag.setVisible(True)

        self.docked_dir = QtWidgets.QDockWidget("Water Direciton", self)
        self.docked_dir.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_dir.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_dir.resize(650, 340)
        self.docked_dir.setWidget(self.web_view_dir)
        self.docked_dir.setVisible(True)

    def shutdown(self):
        """
        Shutdown object.
        :return:
        """
        self.average_thread.shutdown()

    def increment_ens(self, ens_count):
        self.increment_ens_sig.emit(ens_count)

    def avg_taken(self, avg_df):
        self.avg_taken_sig.emit()

        # Update the plot
        self.update_dashboard(avg_df)

    def refresh_wave_height_web_view(self):
        """
        Reload the web view.
        :return:
        """
        self.web_view_wave_height.reload()

    def refresh_earth_east_vel_web_view(self):
        """
        Reload the web view.
        :return:
        """
        self.web_view_earth_east_vel.reload()

    def refresh_earth_north_vel_web_view(self):
        """
        Reload the web view.
        :return:
        """
        self.web_view_earth_north_vel.reload()

    def refresh_mag_web_view(self):
        """
        Reload the web view.
        :return:
        """
        self.web_view_mag.reload()

    def refresh_dir_web_view(self):
        """
        Reload the web view.
        :return:
        """
        self.web_view_dir.reload()

    def add_ens(self, ens):
        """
        Add an ensemble to this view model.

        This will accumulate the ensemble in the Average Water Column
        objects in a dictionary.  When the correct number of ensembles
        have been accumulated, the average will be taken.
        :param ens: Ensemble to accumulate.
        :return:
        """
        # Add data to the thread
        self.average_thread.add_ens(ens)

        #self.stream_plot_earth_vel(ens)

    def reset_average(self):
        """
        Reset the average.
        :return:
        """
        self.average_thread.reset_average()

    def setup_bokeh_server(self, doc):
        """
        Setup the bokeh server in the mainwindow.py.  The server
        must be started on the main thread.
        :param doc:
        :return:
        """

        #renderer = hv.renderer('bokeh')

        #source_df = streamz.dataframe.Random(freq='5ms', interval='100ms')
        #sdf = (source_df - 0.5).cumsum()
        #raw_dmap = hv.DynamicMap(hv.Curve, streams=[self.buffer])
        #raw_dmap = hv.DynamicMap(hv.Curve, streams=[self.dfstream])
        #smooth_dmap = hv.DynamicMap(hv.Curve, streams=[Buffer(sdf.x.rolling('500ms').mean())])


        #layout = (raw_dmap.relabel('raw') * smooth_dmap.relabel('smooth'))

        #app = renderer.app(raw_dmap)
        #doc = renderer.server_doc(raw_dmap)
        #layout = renderer.get_plot(raw_dmap, doc).state
        #doc.title = "Voltage Plot"
        #doc.add_root(layout)

        #p = figure(plot_width=400, plot_height=400, x_axis_type='datetime', title="Voltage")
        #p.x_range.follow_interval = 200
        #p.line(x='date', y='voltage', alpha=0.2, line_width=3, color='navy', source=self.cds)

        #p2 = figure(plot_width=400, plot_height=400, x_axis_type='datetime', title="Heading")
        #p2.x_range.follow_interval = 200
        #p2.line(x='date', y='heading', line_width=2, source=self.cds)

        p_range = figure(plot_width=400, plot_height=400, x_axis_type='datetime', title="Wave Height")
        p_range.x_range.follow_interval = 200
        p_range.xaxis.axis_label = "Time"
        p_range.yaxis.axis_label = "Wave Height (m)"
        p_range.line(x='date', y='wave_height', line_width=2, source=self.cds)

        legend_bin_1 = "Bin" + self.rti_config.config['Waves']['selected_bin_1']
        legend_bin_2 = "Bin" + self.rti_config.config['Waves']['selected_bin_2']
        legend_bin_3 = "Bin" + self.rti_config.config['Waves']['selected_bin_3']

        p_earth_east = figure(plot_width=400, plot_height=400, x_axis_type='datetime', title="Earth Velocity East")
        p_earth_east.x_range.follow_interval = 200
        p_earth_east.xaxis.axis_label = "Time"
        p_earth_east.yaxis.axis_label = "Velocity (m/s)"
        p_earth_east.line(x='date', y='earth_east_1', line_width=2, source=self.cds, legend=legend_bin_1, color='navy')
        p_earth_east.line(x='date', y='earth_east_2', line_width=2, source=self.cds, legend=legend_bin_2, color='skyblue')
        p_earth_east.line(x='date', y='earth_east_3', line_width=2, source=self.cds, legend=legend_bin_3, color='orange')

        p_earth_north = figure(plot_width=400, plot_height=400, x_axis_type='datetime', title="Earth Velocity North")
        p_earth_north.x_range.follow_interval = 200
        p_earth_north.xaxis.axis_label = "Time"
        p_earth_north.yaxis.axis_label = "Velocity (m/s)"
        p_earth_north.line(x='date', y='earth_north_1', line_width=2, source=self.cds, legend=legend_bin_1, color='navy')
        p_earth_north.line(x='date', y='earth_north_2', line_width=2, source=self.cds, legend=legend_bin_2, color='skyblue')
        p_earth_north.line(x='date', y='earth_north_3', line_width=2, source=self.cds, legend=legend_bin_3, color='orange')

        #plot_layout = grid([p_range],
        #              gridplot([[p], [p2]], toolbar_location="left", plot_width=1000),
        #              gridplot([[p_earth_east], [p_earth_north]], toolbar_location="left", plot_width=1000), ncols=3)

        plot_layout = grid([p_range, None, p_earth_north, p_earth_east], ncols=2)

        doc.add_root(plot_layout)
        doc.add_periodic_callback(self.update_live_plot, 500)
        doc.title = "ADCP Dashboard"


        """"
        # Initialize the dataframe
        columns = ['datetime', 'height', 'value']
        df = pd.DataFrame(columns=columns)
        df['datetime'] = pd.to_datetime(df['datetime'])

        # Create a stream for the data
        #self.earth_vel_east_stream = hv.streams.Buffer(df)
        stream = streamz.Stream()
        self.earth_vel_east_stream = streamz.dataframe.DataFrame(stream, example=df)

        # dmap to have a plot with live updates
        self.earth_vel_east_dmap = hv.DynamicMap(hv.Curve, streams=[self.earth_vel_east_stream])

        # Create the plot options
        self.earth_vel_east_plot = self.earth_vel_east_dmap.opts(
            opts.Curve(width=400, height=400, title="Wave Height"))

        plot_panel = pn.Row(self.earth_vel_east_plot)
        plot_panel.show(port=0)

        doc.title = "Earth Velocity Plot"
        doc.add_root(plot_panel)
        #doc.add_root(self.earth_vel_east_plot)

        #renderer = hv.renderer('bokeh')
        #doc = renderer.server_doc(plot_panel)
        #doc.title("Bokeh Server")
        """
        """
        fig = figure(title='Earth Velocity Plot!', sizing_mode='scale_width')
        fig.line(source=self.earth_vel_east_stream, x='x', y='y')

        doc.title = "Now with live updating!"
        doc.add_root(fig)
        """

    def update_live_plot(self):

        date_list = []
        wave_height_list = []
        earth_east_1 = []
        earth_east_2 = []
        earth_east_3 = []
        earth_north_1 = []
        earth_north_2 = []
        earth_north_3 = []
        while self.buffer_datetime:
            date_list.append(self.buffer_datetime.popleft())
        while self.buffer_wave_height:
            wave_height_list.append(self.buffer_wave_height.popleft())
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

        if len(date_list) > 0 and len(wave_height_list) > 0 and len(earth_east_1) > 0 and len(earth_east_2) > 0 and len(earth_east_3) > 0 and len(earth_north_1) > 0 and len(earth_north_2) > 0 and len(earth_north_3) > 0:
            new_data = {'date': date_list,
                        'wave_height': wave_height_list,
                        'earth_east_1': earth_east_1,
                        'earth_east_2': earth_east_2,
                        'earth_east_3': earth_east_3,
                        'earth_north_1': earth_north_1,
                        'earth_north_2': earth_north_2,
                        'earth_north_3': earth_north_3}
            self.cds.stream(new_data)

    def update_dashboard(self, avg_df):
        """
        Dataframe columns: ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "blank", "bin_size", "value"]

        :param avg_df:
        :return:
        """
        #print(avg_df.tail())

        # Wave Height and Datetime
        self.get_wave_height_list(avg_df, self.buffer_wave_height, self.buffer_datetime)

        # Selected bins
        bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
        bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
        bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

        # Earth Velocity
        self.get_earth_vel_list(avg_df, bin_1, 0, self.buffer_earth_east_1)
        self.get_earth_vel_list(avg_df, bin_2, 0, self.buffer_earth_east_2)
        self.get_earth_vel_list(avg_df, bin_3, 0, self.buffer_earth_east_3)
        self.get_earth_vel_list(avg_df, bin_1, 1, self.buffer_earth_north_1)
        self.get_earth_vel_list(avg_df, bin_2, 1, self.buffer_earth_north_2)
        self.get_earth_vel_list(avg_df, bin_3, 1, self.buffer_earth_north_3)

        """ 
        while self.buffer_voltage:
            voltage_list.append(self.buffer_voltage.popleft())
            date_list.append(self.buffer_datetime.popleft())
        while self.buffer_heading:
            heading_list.append(self.buffer_heading.popleft())
        while self.buffer_wave_height:
            wave_height_list.append(self.buffer_wave_height.popleft())
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

        new_data = {'date': date_list,
                    'wave_height': wave_height_list,
                    'earth_east_1': earth_east_1,
                    'earth_east_2': earth_east_2,
                    'earth_east_3': earth_east_3,
                    'earth_north_1': earth_north_1,
                    'earth_north_2': earth_north_2,
                    'earth_north_3': earth_north_3}
        self.cds.stream(new_data)
        """

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
        #for index, row in wave_height_df.iterrows():
        #    buffer_wave.append(row['value'])
        #    buffer_dt.append(row['datetime'])
        last_row = wave_height_df.iloc[:-1]
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

        #for index, row in earth_vel_df.iterrows():
        #    buffer.append(row['value'])
        last_row = earth_vel_df.tail(1)
        if not last_row.empty:
            buffer.append(last_row['value'].values[0])

    def stream_plot_earth_vel(self, ens):
        """
        Create a HTML plot of the Earth Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :return:
        """
        if ens and ens.IsEnsembleData and ens.IsSystemSetup and ens.IsAncillaryData:
            #new = {'datetime': [ens.EnsembleData.datetime()],
            #       'voltage': [ens.SystemSetup.Voltage]}
            #new = {'date': [ens.EnsembleData.datetime()],
            #       'voltage': [ens.SystemSetup.Voltage]}
            #self.stream.stream(new)
            #self.earth_df = self.earth_df.append(new, ignore_index=True)
            #self.stream.stream.start()
            #self.dfstream.send(self.earth_df)
            #self.dfstream.update()
            #self.cds.stream(new)
            self.buffer_voltage.append(ens.SystemSetup.Voltage)
            self.buffer_datetime.append(ens.EnsembleData.datetime())
            self.buffer_heading.append(ens.AncillaryData.Heading)
            self.buffer_wave_height.append(ens.AncillaryData.TransducerDepth)

        bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])
        bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])
        bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])
        if ens and ens.IsEarthVelocity:
            self.buffer_earth_east_1.append(ens.EarthVelocity.Velocities[bin_1][0])
            self.buffer_earth_east_2.append(ens.EarthVelocity.Velocities[bin_2][0])
            self.buffer_earth_east_3.append(ens.EarthVelocity.Velocities[bin_3][0])
            self.buffer_earth_north_1.append(ens.EarthVelocity.Velocities[bin_1][1])
            self.buffer_earth_north_2.append(ens.EarthVelocity.Velocities[bin_2][1])
            self.buffer_earth_north_3.append(ens.EarthVelocity.Velocities[bin_3][1])

        # Sort the data for only the "EarthVel" data type
        #selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.bin_num == bin_num)]
        #selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel") & avg_df.beam_num == beam_num)]

        #if self.earth_vel_east_stream:
            #self.earth_vel_east_stream.send(selected_avg_df)
        #    self.earth_vel_east_stream.emit(selected_avg_df)

            # Save the plot to a file
        #    hv.save(self.earth_vel_east_plot, self.earth_vel_html_file, fmt='html')

        # Create the plot if it does not exist
        #if not self.earth_vel_east_stream:
        #    self.earth_vel_east_stream = hv.streams.Buffer(selected_avg_df)
        #    self.earth_vel_east_dmap = hv.DynamicMap(hv.Curve, streams=[self.earth_vel_east_stream])

        #    self.earth_vel_east_plot = self.earth_vel_east_dmap.opts(
        #        opts.Curve(width=800, height=800, title="Earth Velocity East"))
        #    renderer = hv.renderer('bokeh')
            #renderer = renderer.instance(mode='server')
            #doc = renderer.server_doc(self.earth_vel_east_plot)

            #app = renderer.app(self.earth_vel_east_dmap)

            # Start Event Loop needed for server
            #asyncio.set_event_loop(asyncio.new_event_loop())

            #server = Server({'/': app}, port=0)

            #server.io_loop.add_callback(server.show, "/")
            #server.io_loop.start()

            #server.start()
            #server.show('/')

            #loop = IOLoop.current()
            #loop.start()

            #server = renderer.app(self.earth_vel_east_dmap, show=True)

            #plot_panel = pn.Row(self.earth_vel_east_plot)
            #plot_panel.show(port=0)

    def add_tab(self, key, web_view):
        """
        Add a Tab to the display
        :param key:
        :return:
        """
        # Create tab
        tab1 = QWidget()
        self.tabWidget.addTab(tab1, key)
        tab1.layout = QVBoxLayout(self)
        tab1.setLayout(tab1.layout)
        tab1.setAccessibleName(key)

        tab1.layout.addWidget(web_view)

        # Set the tab index for the dictionary to keep track of all the tabs
        self.tab_dict[key] = len(self.tabWidget)-1

    def populate_table(self, key, avg_vel):
        if key in self.tab_dict:

            self.populate_beam_table(key, avg_vel)
            #self.populate_earth_table(key, avg_vel)

    def populate_beam_table(self, key, avg_vel):
        tab_index = self.tab_dict[key]
        tab = self.tabWidget.widget(tab_index)
        table_widget = tab.layout.itemAt(0).widget()  # There is only 1 widget, the table

        if avg_vel[AverageWaterColumn.INDEX_BEAM] and avg_vel[AverageWaterColumn.INDEX_BEAM][0]:
            num_bins = len(avg_vel[AverageWaterColumn.INDEX_BEAM])
            num_beams = len(avg_vel[AverageWaterColumn.INDEX_BEAM][0])

            # Set the number of rows based off the numbers bins
            table_widget.setRowCount(num_bins)
            table_widget.setColumnCount(num_beams)

            # Add Earth data to the row
            if avg_vel[AverageWaterColumn.INDEX_BEAM]:
                for bin_num in range(num_bins):
                    for beam_num in range(num_beams):
                        #print(num_bins, num_beams, table_widget.rowCount(), table_widget.columnCount(), len(avg_vel[AverageWaterColumn.INDEX_BEAM]), len(avg_vel[AverageWaterColumn.INDEX_BEAM][0]), bin_num, beam_num)
                        table_widget.setItem(bin_num, beam_num, QTableWidgetItem(avg_vel[AverageWaterColumn.INDEX_BEAM][bin_num][beam_num]))

            table_widget.viewport().update()

    def populate_earth_table(self, key, avg_vel):
        tab_index = self.tab_dict[key]
        tab = self.tabWidget.widget(tab_index)
        table_widget = tab.layout.itemAt(0).widget()  # There is only 1 widget, the table

        if avg_vel[AverageWaterColumn.INDEX_EARTH] and avg_vel[AverageWaterColumn.INDEX_EARTH][0]:
            num_bins = len(avg_vel[AverageWaterColumn.INDEX_EARTH])
            num_beams = len(avg_vel[AverageWaterColumn.INDEX_EARTH][0])

            # Set the number of rows based off the numbers bins
            table_widget.setRowCount(num_bins)
            table_widget.setColumnCount(num_beams)

            # Add Earth data to the row
            if avg_vel[AverageWaterColumn.INDEX_EARTH]:
                for bin_num in range(num_bins):
                    for beam_num in range(num_beams):
                        table_widget.setItem(bin_num, beam_num, QTableWidgetItem(avg_vel[AverageWaterColumn.INDEX_EARTH][bin_num][beam_num]))

    def plot_ens(self, ens):
        # Ensemble number
        self.ens_num.append(ens.EnsembleData.EnsembleNumber)

        mag_data = []
        east = 0.0
        north = 0.0
        vert = 0.0
        bt_east = 0.0
        bt_north = 0.0
        bt_vert = 0.0

        # Set the number of bins
        self.num_bins = ens.EnsembleData.NumBins

        for bin_num in range(ens.EnsembleData.NumBins):
            if ens.BeamVelocity.element_multiplier > 3:
                if ens.EarthVelocity.Velocities[bin_num][0] >= ens.BadVelocity or ens.EarthVelocity.Velocities[bin_num][1] >= ens.BadVelocity or ens.EarthVelocity.Velocities[bin_num][2] >= ens.BadVelocity:
                    # If earth velocity is bad for the bin, set to 0.0
                    mag_data.append(0.0)
                else:
                    # Get Bottom Track data if good
                    if ens.IsBottomTrack:
                        if ens.BottomTrack.EarthVelocity[0] < ens.BadVelocity and ens.BottomTrack.EarthVelocity[1] < ens.BadVelocity and ens.BottomTrack.EarthVelocity[2] < ens.BadVelocity:
                            bt_east = ens.BottomTrack.EarthVelocity[0]
                            bt_north = ens.BottomTrack.EarthVelocity[1]
                            bt_vert = ens.BottomTrack.EarthVelocity[2]

                    # Remove the ship speed
                    east = ens.EarthVelocity.Velocities[bin_num][0] + bt_east
                    north = ens.EarthVelocity.Velocities[bin_num][0] + bt_north
                    vert = ens.EarthVelocity.Velocities[bin_num][0] + bt_vert

                    # Calculate the magnitude
                    mag = math.sqrt(east ** 2 + north ** 2 + vert ** 2)

                    # Accumulate the mag data for this ensemble
                    mag_data.append(mag)

        # Accumulate the data for each ensemble
        self.data.append(mag_data)

    def create_plot(self):
        # output to static HTML file
        output_file(self.HTML_FILE_NAME)

        df = pd.DataFrame(
            self.data,
            columns=range(self.num_bins),
            # columns=Range1d(start=num_bins, end=0),
            index=self.ens_num)
        df.index.name = 'ens_num'
        df.columns.name = 'bins'
        # Prepare data.frame in the right format
        df = df.stack().rename("value").reset_index()

        # create a new plot with a title and axis labels
        hm = figure(title="Water Magnitude (m/s)",
                    # tools="hover",
                    toolbar_location=None)

        mapper = LinearColorMapper(palette=Inferno256, low=df.value.min(), high=df.value.max())

        hm.rect(x="ens_num",
                    y="bins",
                    width=1,
                    height=1,
                    source=df,
                    #fill_color=transform('value', mapper),
                    #fill_color=mapper,
                    fill_color={'field': 'value', 'transform': mapper},
                    line_color=None)

        color_bar = ColorBar(color_mapper=mapper,
                             major_label_text_font_size="5pt",
                             # ticker=BasicTicker(desired_num_ticks=len(colors)),
                             # ticker=BasicTicker(desired_num_ticks=6),
                             formatter=PrintfTickFormatter(format="%d"),
                             label_standoff=6,
                             border_line_color=None,
                             location=(0, 0))
        hm.add_layout(color_bar, 'right')

        hm.add_tools(HoverTool(
            tooltips=[("vel", "@value"), ("(bin,ens)", "(@bins, @ens_num)")],
            mode="mouse",
            point_policy="follow_mouse"
        ))

        # Save the plot to html
        save(hm)

