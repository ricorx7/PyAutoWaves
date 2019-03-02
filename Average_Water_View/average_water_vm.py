from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
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

from . import average_water_view
import logging
from obsub import event
import os
from rti_python.Utilities.config import RtiConfig


class AverageWaterVM(average_water_view.Ui_AvgWater, QWidget):


    #add_ens_sig = pyqtSignal(object)

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
        #self.rti_config.init_water_average_config()

        # Setup Signal
        #self.add_ens_sig.connect(self.add_ens)

        self.html = None
        self.web_view = QWebEngineView()
        #self.web_view.loadFinished.connect(self._loadFinished)
        #elf.web_view.load(QUrl("www.google.com"))
        #while self.html is None:
        #    logging.debug("Waiting")
        html_path = os.path.split(os.path.abspath(__file__))[0] + os.sep + ".." + os.sep + self.HTML_FILE_NAME
        #html_path = self.HTML_FILE_NAME
        print(html_path)
        self.web_view.load(QUrl().fromLocalFile(html_path))

        self.init_display()

    #def _callable(self, data):
    #    self.html = data

    #def _loadFinished(self, result):
    #    self.web_view.page().toHtml(self._callable)

    def init_display(self):
        self.tableWidget.setToolTip("Average Water Column")
        self.horizontalLayout.addWidget(self.web_view)

        self.tableWidget.setRowCount(200)
        self.tableWidget.setColumnCount(1)
        self.tableWidget.setHorizontalHeaderLabels(['Average Water Column'])

    def add_ens(self, ens):
        self.process_ens(ens)
        #self.create_plot()
        #self.web_view.reload()

    def process_ens(self, ens):
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

