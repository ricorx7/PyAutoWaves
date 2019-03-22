from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QUrl, QEventLoop
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from bokeh.plotting import figure, output_file, show, save
from bokeh.models import LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar
from bokeh.transform import transform, linear_cmap
from bokeh.palettes import Viridis3, Viridis256, Inferno256
from bokeh.models import HoverTool
from bokeh.models import Range1d
import math
import pandas as pd
import numpy as np
from threading import Thread
import threading
import csv
import datetime

from . import average_water_view
import logging
from obsub import event
import os
from rti_python.Utilities.config import RtiConfig
from rti_python.Ensemble.Ensemble import Ensemble
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn

# pyviz
import numpy as np
import scipy.stats as ss
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')

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
    refresh_web_view_sig = pyqtSignal()

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
        self.csv_file_index = 1
        self.num_bins = 30
        self.ens_num = []
        self.data = []

        # Web Views
        self.web_view_wave_height = QWebEngineView()

        # Setup signal
        self.add_tab_sig.connect(self.add_tab)
        self.populate_table_sig.connect(self.populate_table)
        self.reset_avg_sig.connect(self.reset_average)
        self.refresh_web_view_sig.connect(self.refresh_web_view)

        # Dictionary to hold all the average water column objects
        self.awc_dict = {}
        self.tab_dict = {}

        # Latest Average Water Column
        self.avg_counter = 0

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

        #self.tableWidget.setRowCount(200)
        #self.tableWidget.setColumnCount(5)
        #self.tableWidget.setHorizontalHeaderLabels(['Average Water Column'])

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

        # Accumulate the water column data
        self.accumulate_ens(ens)

        # Check if it is time to average data
        if self.avg_counter >= int(self.rti_config.config['AWC']['num_ensembles']):
            thread = Thread(target=self.average_and_display)
            thread.start()
            thread.join(1000)

    def average_and_display(self):
        """
        Average the data and display the data.
        :param awc_key: Average Water Column key to find the correct tables.
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
        self.display_data("")

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

    def display_data(self, file_index):

        # Read in the CSV data of the average data
        avg_df = pd.read_csv(self.csv_file_path)

        # Update the Wave Height Plot
        self.plot_wave_height(avg_df)

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
        selected_avg_df = avg_df[avg_df.data_type.str.contains("XdcrDepth")]

        # Set the dependent
        vdims = [('value', 'Values')]

        # Set the independent columns
        # Create the Holoview dataset
        ds = hv.Dataset(selected_avg_df, ['datetime'], vdims)

        # Plot and select a bin
        pressure_xdcr_height = ds.to(hv.Curve, 'datetime', 'value') + hv.Table(ds)

        # Save the plot to a file
        hv.save(pressure_xdcr_height, self.wave_height_html_file, fmt='html')

        # Refresh the web view
        #self.web_view_wave_height.reload()
        self.refresh_web_view_sig.emit()

    def refresh_web_view(self):
        self.web_view_wave_height.reload()

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
            with open(self.csv_file_path , 'a', newline='') as csv_file:
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

        # Create the file name
        file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        # Look if the file exist, if it does, make sure it is less than max file size
        while os.path.isfile(file_path) and os.path.getsize(file_path) >= max_file_size:
            self.csv_file_index += 1
            file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + "A" + str(self.csv_file_index).zfill(5) + self.CSV_FILE_EXT

        if not os.path.exists(file_path):
            header = ["datetime", "data_type", "ss_code", "ss_config", "bin_num", "beam_num", "bin_depth", "value"]

            with open(file_path, 'w', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)
                wr.writerow(header)

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

