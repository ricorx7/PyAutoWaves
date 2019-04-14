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
import holoviews as hv
import streamz
import streamz.dataframe
import asyncio

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

        self.HTML_FILE_NAME = "Earth.html"
        self.CSV_AVG_FILE_NAME = "average_data.csv"
        self.CSV_FILE_EXT = ".csv"
        self.csv_file_path = ""                # Latest CSV file path
        self.wave_height_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "WaveHeight"
        self.earth_vel_html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "EarthVel"
        self.csv_file_index = 1
        self.num_bins = 30
        self.ens_num = []
        self.data = []
        self.csv_creation_date = datetime.datetime.now()

        self.ens_queue = collections.deque()
        self.display_eventt = threading.Event()
        self.display_thread_alive = True
        self.display_thread = threading.Thread(name="avg_water_vm", target=self.thread_display_run)
        self.display_thread.start()

        # Web Views
        self.web_view_wave_height = QWebEngineView()
        self.web_view_earth_vel = QWebEngineView()

        # Setup signal
        self.add_tab_sig.connect(self.add_tab)
        self.populate_table_sig.connect(self.populate_table)
        self.reset_avg_sig.connect(self.reset_average)
        self.refresh_wave_height_web_view_sig.connect(self.refresh_wave_height_web_view)
        self.refresh_earth_vel_web_view_sig.connect(self.refresh_earth_vel_web_view)

        # Dictionary to hold all the average water column objects
        self.awc_dict = {}
        self.tab_dict = {}

        # Latest Average Water Column
        self.avg_counter = 0

        self.earth_vel_east_stream = None
        self.earth_vel_east_dmap = None
        self.earth_vel_east_plot = None

        #self.html = None
        #self.web_view = QWebEngineView()
        #html_path = os.path.split(os.path.abspath(__file__))[0] + os.sep + ".." + os.sep + self.HTML_FILE_NAME
        #html_path = self.wave_height_html_file + ".html"
        #print(html_path)
        #self.web_view.load(QUrl().fromLocalFile(html_path))

        #self.add_tab("Wave Height")

        self.init_display()

    #def _callable(self, data):
    #    self.html = data

    #def _loadFinished(self, result):
    #    self.web_view.page().toHtml(self._callable)

    def init_display(self):
        #self.tableWidget.setToolTip("Average Water Column")
        #self.horizontalLayout.addWidget(self.web_view)
        self.tabWidget.clear()
        self.setWindowTitle("Average Water Column")

        self.web_view_wave_height.load(QUrl().fromLocalFile(self.wave_height_html_file + ".html"))
        self.add_tab_sig.emit("Wave Height", self.web_view_wave_height)

        self.web_view_earth_vel.load(QUrl().fromLocalFile(self.earth_vel_html_file + ".html"))
        self.add_tab_sig.emit("Earth Velocity", self.web_view_earth_vel)

        self.docked_wave_height = QtWidgets.QDockWidget("Wave Height", self)
        self.docked_wave_height.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_wave_height.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_wave_height.resize(1100, 400)
        self.docked_wave_height.setWidget(self.web_view_wave_height)
        self.docked_wave_height.setVisible(True)
        #self.addDockWidget(QtCore.Qt.AllDockWidgetAreas, self.docked_wave_height)

        self.docked_earth_vel_east = QtWidgets.QDockWidget("Earth Velocity - East", self)
        self.docked_earth_vel_east.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_earth_vel_east.setFeatures(
            QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_earth_vel_east.resize(1100, 400)
        self.docked_earth_vel_east.setWidget(self.web_view_earth_vel)
        self.docked_earth_vel_east.setVisible(True)
        #self.addDockWidget(QtCore.Qt.AllDockWidgetAreas, self.docked_wave_height)

        #self.tableWidget.setRowCount(200)
        #self.tableWidget.setColumnCount(5)
        #self.tableWidget.setHorizontalHeaderLabels(['Average Water Column'])

        # Create Streaming plot
        #self.earth_vel_east_source = streamz.Stream()
        #pipe = Pipe(data=pd.DataFrame({'x': [], 'y': [], 'count': []}))
        #self.earth_vel_east_source.sliding_window(20).map(pd.concat).sink(pipe.send)  # Connect streamz to the Pipe
        #self.earth_vel_plot = hv.DynamicMap(hv.Curve, streams=[pipe])

    def shutdown(self):
        self.display_thread_alive = False
        self.display_eventt.set()
        self.display_thread.join()

    def add_ens(self, ens):
        """
        Add an ensemble to this view model.

        This will accumulate the ensemble in the Average Water Column
        objects in a dictionary.  When the correct number of ensembles
        have been accumulated, the average will be taken.
        :param ens: Ensemble to accumulate.
        :return:
        """
        #self.plot_ens(ens)
        #self.create_plot()
        #self.web_view.reload()

        # Add data to the queue
        #start = time.clock()
        self.ens_queue.append(ens)
        #print("Add Que: " + str(time.clock()-start))

        print(threading.current_thread().getName() + " data added")

        #start = time.clock()
        # Emit a signal that an ensemble was added
        self.increment_ens_sig.emit(self.avg_counter)
        #print("increment sig: " + str(time.clock()-start))

        # Wakekup the thread
        self.display_eventt.set()


        # Accumulate the water column data
        #self.accumulate_ens(ens)

        # Check if it is time to average data
        #if self.avg_counter >= int(self.rti_config.config['AWC']['num_ensembles']):
            #thread = Thread(target=self.average_and_display)
            #thread.start()
            #thread.join()
        #    self.average_and_display()


    def thread_display_run(self):

        while self.display_thread_alive:

            if self.display_eventt.is_set():

            # Wait to be woken up
            self.display_eventt.wait()

            print(threading.current_thread().getName() + " " + str(len(self.ens_queue)))

            while len(self.ens_queue) > 0:
                # Remove the ensemble from the queue
                ens = self.ens_queue.popleft()

                # Accumulate the water column data
                start = time.clock()
                self.accumulate_ens(ens)
                print("Accum : " + str(time.clock()-start))

                # Check if it is time to average data
                if self.avg_counter >= int(self.rti_config.config['AWC']['num_ensembles']):
                    #thread = Thread(target=self.average_and_display)
                    #thread.start()
                    #thread.join()
                    start = time.clock()
                    self.average_and_display()
                    print("avg and display : " + str(time.clock() - start))


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

        # Update the display
        #self.populate_table_sig.emit(awc_key, awc_average)

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
        self.plot_wave_height(avg_df)

        # Update the Earth Vel Plot East
        self.plot_earth_vel(avg_df,
                            0,
                            int(self.rti_config.config['Waves']['selected_bin_1']),
                            int(self.rti_config.config['Waves']['selected_bin_2']),
                            int(self.rti_config.config['Waves']['selected_bin_3']))

        #self.stream_plot_earth_vel(avg_df,
        #                    0,
        #                    int(self.rti_config.config['Waves']['selected_bin_1']),
        #                    int(self.rti_config.config['Waves']['selected_bin_2']),
        #                    int(self.rti_config.config['Waves']['selected_bin_3']))

        """
        # Update the Earth Vel Plot North
        self.plot_earth_vel(avg_df,
                            1,
                            int(self.rti_config.config['Waves']['selected_bin_1']),
                            int(self.rti_config.config['Waves']['selected_bin_2']),
                            int(self.rti_config.config['Waves']['selected_bin_3']))
        
        # Update the Earth Vel Plot Vertical
        self.plot_earth_vel(avg_df,
                            2,
                            int(self.rti_config.config['Waves']['selected_bin_1']),
                            int(self.rti_config.config['Waves']['selected_bin_2']),
                            int(self.rti_config.config['Waves']['selected_bin_3']))
        """


        #selected_avg_df = avg_df[avg_df.data_type.str.contains("Pressure") | avg_df.data_type.str.contains("XdcrDepth")]

        # Set the dependent
        #vdims = [('value', 'Values')]

        # Set the independent columns
        # Create the Holoview dataset
        #ds = hv.Dataset(selected_avg_df, ['datetime', 'data_type', 'ss_code', 'ss_config', 'bin_num', 'beam_num'], vdims)
        #print(ds)

        # Plot and select a bin
        #pressure_xdcr_height = ds.to(hv.Curve, 'datetime', 'value', ['data_type']) + hv.Table(ds)
        #pressure_xdcr_height = ds.to(hv.Curve, 'datetime', 'value')


        #print(curves)

        # Set the options for the plot
        #pressure_xdcr_height.opts(
        #    opts.Curve(width=600, height=250, framewise=True, tools=['hover']))


        # Save to HTML
        #hv.save(pressure_xdcr_height, self.wave_height_html_file, fmt='html')

        # Plot and list the bins
        #subset = macro.select(bin_num=[1, 3, 5])
        #curves = subset.to(hv.Curve, 'datetime', 'value').layout()


        # Render the plot
        #renderer = hv.renderer('bokeh')

        # Pressure and Wave Height Plot
        #renderer.save(pressure_xdcr_height, wave_height_html_file)
        #plot = renderer.get_plot(curves).state

        #save(pressure_xdcr_height, wave_height_html_file)
        # or
        #output_file(html_file)
        #show(plot)
        #show(pressure_xdcr_height)

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
        vdims = [('value', 'Wave Height (m)')]

        # Plot and select a bin
        pressure_xdcr_height = hv.Curve(selected_avg_df, kdims, vdims) + hv.Table(selected_avg_df)

        # Save the plot to a file
        hv.save(pressure_xdcr_height, self.wave_height_html_file, fmt='html')

        # Refresh the web view
        self.refresh_wave_height_web_view_sig.emit()

    def plot_earth_vel(self, avg_df, beam_num, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Earth Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :return:
        """
        # Sort the data for only the "EarthVel" data type
        #selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.bin_num == bin_num)]
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel"))]

        # Remove all the columns except datetime and value
        #selected_avg_df = selected_avg_df[['datetime', 'bin_num', 'beam_num', 'value']]

        # Set independent variables or index
        kdims = [('datetime', 'Date and Time'), ('bin_num', 'bin'), 'ss_code', 'ss_config']

        # Set the dependent variables or measurements
        vdims = [('value', 'Water Velocity (m/s)')]

        # Set the independent columns
        # Create the Holoview dataset
        ds = hv.Dataset(selected_avg_df, kdims, vdims)

        # Plot and select a bin
        #plot = ds.to(hv.Curve, 'datetime', 'value', groupby='bin_num') + hv.Table(ds)
        #plot = hv.Curve(selected_avg_df, kdims, vdims) + hv.Table(selected_avg_df)

        bin_list = []
        bin_list.append(selected_bin_1)
        #bin_list.append(selected_bin_2)
        #bin_list.append(selected_bin_3)
        subset = ds.select(bin_num=bin_list, beam_num=0)
        #plot = subset.to(hv.Curve, 'datetime', 'value').layout()
        #plot.opts(opts.Curve(width=400, height=400, title='Earth Velocity Data'))

        # Title
        title = "Earth Velocity East - [Bin " + str(selected_bin_1) + "]"

        # Create the plot options
        plot = (subset.to(hv.Curve, 'datetime', 'value') + hv.Table(subset)).opts(
            opts.Curve(width=400, height=400, title=title))

        # Save the plot to a file
        hv.save(plot, self.earth_vel_html_file, fmt='html')

        # Save the plot to a file
        # Include the group by
        #hv.renderer('bokeh').save(plot, self.earth_vel_html_file, fmt='scrubber')

        # Refresh the web view
        self.refresh_earth_vel_web_view_sig.emit()

    def setup_bokeh_server(self, doc):
        """
        Setup the bokeh server in the mainwindow.py.  The server
        must be started on the main thread.
        :param doc:
        :return:
        """
        # Initialize the dataframe
        columns = ['datetime', 'data_type', 'ss_code', 'ss_config', 'bin_num', 'beam_num', 'bin_depth', 'value']
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
            opts.Curve(width=400, height=400, title="Earth Velocity East"))

        plot_panel = pn.Row(self.earth_vel_east_plot)
        plot_panel.show(port=0)

        doc.add_root(plot_panel)
        #doc.add_root(self.earth_vel_east_plot)

    def stream_plot_earth_vel(self, avg_df, beam_num, selected_bin_1, selected_bin_2, selected_bin_3):
        """
        Create a HTML plot of the Earth Velocity data from the
        CSV file.
        :param avg_df:  Dataframe of the csv file
        :return:
        """
        # Sort the data for only the "EarthVel" data type
        #selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel")) & (avg_df.bin_num == bin_num)]
        selected_avg_df = avg_df[(avg_df.data_type.str.contains("EarthVel") & avg_df.beam_num == beam_num)]

        if self.earth_vel_east_stream:
            #self.earth_vel_east_stream.send(selected_avg_df)
            self.earth_vel_east_stream.emit(selected_avg_df)

            # Save the plot to a file
            #hv.save(self.earth_vel_east_plot, self.earth_vel_html_file, fmt='html')

        # Create the plot if it does not exist
        #if not self.earth_vel_east_stream:
        #    self.earth_vel_east_stream = hv.streams.Buffer(selected_avg_df)
        #    self.earth_vel_east_dmap = hv.DynamicMap(hv.Curve, streams=[self.earth_vel_east_stream])

         #   self.earth_vel_east_plot = self.earth_vel_east_dmap.opts(
         #       opts.Curve(width=800, height=800, title="Earth Velocity East"))
         #   renderer = hv.renderer('bokeh')
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

    def refresh_wave_height_web_view(self):
        self.web_view_wave_height.reload()

    def refresh_earth_vel_web_view(self):
        self.web_view_earth_vel.reload()

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

                    # Add the new tab for each subsystem configuration
                    #self.add_tab_sig.emit(key)

                # Add the ensemble to the correct AverageWaterColumn
                self.awc_dict[key].add_ens(ens)

                # Emit a signal that an ensemble was added
                self.increment_ens_sig.emit(self.avg_counter)

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

