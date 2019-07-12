from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QVBoxLayout
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QUrl, QEventLoop
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import QtGui, QtWidgets, QtCore
from bokeh.plotting import figure, output_file, show, save
from bokeh.models import LinearColorMapper, BasicTicker, PrintfTickFormatter, ColorBar
from bokeh.palettes import Viridis3, Viridis256, Inferno256
from bokeh.models import HoverTool
from .average_water_thread import AverageWaterThread
from .plot_average_data import PlotAverageData
from .bokeh_plot_manager import BokehPlotManager
from .plot_hv_average_data import PlotHvAverageData
import math
from . import average_water_view
from rti_python.Post_Process.Average.AverageWaterColumn import AverageWaterColumn
import pandas as pd
import holoviews as hv
from holoviews import opts, dim, Palette
hv.extension('bokeh')
import panel as pn
pn.extension()
from bokeh.plotting import figure, ColumnDataSource
opts.defaults(
    opts.Bars(xrotation=45, tools=['hover']),
    opts.BoxWhisker(width=800, xrotation=30, box_fill_color=Palette('Category20')),
    opts.Curve(width=600, tools=['hover']),
    opts.GridSpace(shared_yaxis=True),
    opts.Scatter(width=800, height=400, color=Palette('Category20'), size=dim('growth')+5, tools=['hover']),
    opts.NdOverlay(legend_position='left'))


class AverageWaterVM(average_water_view.Ui_AvgWater, QWidget):

    increment_ens_sig = pyqtSignal(int)
    reset_avg_sig = pyqtSignal()
    avg_taken_sig = pyqtSignal()

    def __init__(self, parent, rti_config):
        average_water_view.Ui_AvgWater.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.rti_config = rti_config
        self.rti_config.init_average_waves_config()

        self.average_thread = AverageWaterThread(self.rti_config, self)
        self.average_thread.setObjectName("Average Water Column Thread")
        self.average_thread.increment_ens_sig.connect(self.increment_ens)
        self.average_thread.avg_taken_sig.connect(self.avg_taken)
        self.average_thread.start()

        # Create the plots
        #self.plot_data = PlotAverageData(rti_config)
        self.plot_data = BokehPlotManager(rti_config)
        self.plot_data.start()
        #self.plot_data = PlotHvAverageData(rti_config)

        # Latest Average Water Column
        self.avg_counter = 0

        # Latest CSV file
        self.latest_csv_file = ""

        self.setWindowTitle("Average Water Column")

    def shutdown(self):
        """
        Shutdown object.
        :return:
        """
        self.average_thread.shutdown()
        self.plot_data.shutdown()

    def set_latest_csv_file(self, file_path):
        """
        Set the latest CSV file path.
        :param file_path: Latest CSV file path.
        :return:
        """
        self.plot_data.set_csv_file(file_path)
        self.latest_csv_file = file_path

    def increment_ens(self, ens_count):
        self.increment_ens_sig.emit(ens_count)

    def avg_taken(self, avg_df):
        """
        Handle the Average being taken.
        This will update the progress bar and update the plot
        with the latest data.
        :param avg_df:
        :return:
        """

        # Update the progress bar
        if int(self.rti_config.config['AWC']['num_ensembles']) > 1:
            self.avg_taken_sig.emit()

        # Update the plot
        if self.rti_config.config.getboolean('PLOT', 'LIVE'):
            self.plot_data.update_dashboard(avg_df)

    def plot_ens(self, ens):
        """
        Plot the ensemble given.
        :param ens: Ensemble data
        :return:
        """

        # Update the plot
        if self.rti_config.config.getboolean('PLOT', 'LIVE'):
            self.plot_data.plot_ens(ens)

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

        #self.reset_plot()

    def reset_plot(self):
        self.create_bokeh_plots()

    def setup_bokeh_server(self, doc):
        self.plot_data.setup_bokeh_server(doc)

