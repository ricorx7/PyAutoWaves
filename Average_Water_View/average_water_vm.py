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
import csv
import datetime

from . import average_water_view
import logging
from obsub import event
import os
from rti_python.Utilities.config import RtiConfig
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
    add_tab_sig = pyqtSignal(str)
    populate_table_sig = pyqtSignal(str, object)

    def __init__(self, parent, rti_config):
        average_water_view.Ui_AvgWater.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.HTML_FILE_NAME = "avg_water_heatmap.html"
        self.num_bins = 30
        self.ens_num = []
        self.data = []

        self.rti_config = rti_config
        self.rti_config.init_average_waves_config()

        # Setup signal
        self.add_tab_sig.connect(self.add_tab)
        self.populate_table_sig.connect(self.populate_table)

        # Dictionary to hold all the average water column objects
        self.awc_dict = {}
        self.tab_dict = {}

        # Latest Average Water Column
        self.avg_counter = 0

        self.html = None
        self.web_view = QWebEngineView()
        html_path = os.path.split(os.path.abspath(__file__))[0] + os.sep + ".." + os.sep + self.HTML_FILE_NAME
        print(html_path)
        self.web_view.load(QUrl().fromLocalFile(html_path))

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
        for awc_key in self.awc_dict.keys():
            if len(self.awc_dict[awc_key].ens_beam_list) >= int(self.rti_config.config['AWC']['num_ensembles']):
                # Create a thread to take the average
                thread = Thread(target=self.average_and_display, args=(awc_key, ))
                thread.start()
                thread.join(1000)

    def average_and_display(self, awc_key):
        """
        Average the data and display the data.
        :param awc_key: Average Water Column key to find the correct tables.
        :return:
        """
        # Average the data
        awc_average = self.awc_dict[awc_key].average()

        # Update CSV file
        self.write_csv(awc_average, awc_key)

        # Update the display
        #self.populate_table_sig.emit(awc_key, awc_average)

        # Display data
        self.display_data(awc_key)

    def display_data(self, awc_key):

        file_title = "earth_east_"
        file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + file_title + awc_key + ".csv"
        html_file = self.rti_config.config['AWC']['output_dir'] + os.sep + "Earth_bin1.html"

        macro_df = pd.read_csv(file_path)
        print(macro_df.head())
        macro = hv.Dataset(macro_df, ['datetime', 'Bin 1'])
        print(macro)

        curves = macro.to(hv.Curve, 'datetime', 'Bin 1')
        print(curves)

        # Render the plot
        renderer = hv.renderer('bokeh')
        renderer.save(curves, html_file)
        plot = renderer.get_plot(curves).state

        save(plot, html_file)
        # or
        output_file(html_file)
        show(plot)

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
                self.add_tab_sig.emit(key)

            return self.awc_dict[key].add_ens(ens)
        else:
            return None

    def write_csv(self, awc_vel, awc_key):
        """
        Write all the CSV data.
        :param awc_vel: Average Velocity data
        :param awc_key: Key to identify the subsystem and config.
        :return:
        """
        self.write_csv_data(awc_vel[AverageWaterColumn.INDEX_EARTH], awc_key, 0, "earth_east_")
        self.write_csv_data(awc_vel[AverageWaterColumn.INDEX_EARTH], awc_key, 1, "earth_north_")
        self.write_csv_data(awc_vel[AverageWaterColumn.INDEX_EARTH], awc_key, 2, "earth_vertical_")

    def write_csv_data(self, awc_vel, awc_key, beam_index, file_title):
        """
        Append the data to the CSV file.
        :param awc_vel: Average Velocity data for all beams.
        :param awc_key: Key used to give the file an identifier for the subsystem and config.
        :param beam_index: Beam index within the velocity data.
        :param file_title: Title to use for the file name.
        :return:
        """
        # Check if the file exist, if it does not, create the file and add the first row
        file_path = self.rti_config.config['AWC']['output_dir'] + os.sep + file_title + awc_key + ".csv"
        self.check_or_create_file(file_path)

        # Get the data
        awc_bin_data = [datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S:%f')]
        for data in awc_vel:
            awc_bin_data.append(str(data[beam_index]))

        # Write the data to the CSV file
        # Added newline='' to ensure no extra lines included
        with open(file_path, 'a', newline='') as csv_file:
            wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)
            wr.writerow(awc_bin_data)

    def check_or_create_file(self, file_path):
        """
        Check if the file exist.  If it does not exist,
        create the file.
        :param file_path: File path to create
        :return:
        """
        if not os.path.exists(file_path):
            bins = ["datetime"]
            for bin_num in range(1, 200):
                bins.append("Bin " + str(bin_num))

            with open(file_path, 'w', newline='') as csv_file:
                wr = csv.writer(csv_file, delimiter=',', quoting=csv.QUOTE_ALL)
                wr.writerow(bins)

    def add_tab(self, key):
        # Create tab
        tab1 = QWidget()
        self.tabWidget.addTab(tab1, key)
        tab1.layout = QVBoxLayout(self)
        table1 = QTableWidget()
        tab1.layout.addWidget(table1)
        tab1.setLayout(tab1.layout)
        tab1.setAccessibleName(key)

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

