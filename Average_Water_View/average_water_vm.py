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

        # Create the plots
        self.plot_data = PlotAverageData(rti_config)

        self.wave_height_html_file = self.average_thread.wave_height_html_file
        self.earth_east_vel_html_file = self.average_thread.earth_east_vel_html_file
        self.earth_north_vel_html_file = self.average_thread.earth_north_vel_html_file
        self.mag_html_file = self.average_thread.mag_html_file
        #self.dir_html_file = self.average_thread.dir_html_file
        self.dir_html_file = "http://localhost:5001/"

        # Web Views
        self.web_view_wave_height = QWebEngineView()
        self.web_view_earth_east_vel = QWebEngineView()
        self.web_view_earth_north_vel = QWebEngineView()
        self.web_view_mag = QWebEngineView()
        self.web_view_dir = QWebEngineView()

        # Latest Average Water Column
        self.avg_counter = 0


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
        self.plot_data.update_dashboard(avg_df)

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

        #self.reset_plot()

    def reset_plot(self):
        self.create_bokeh_plots()

    def setup_bokeh_server(self, doc):
        self.plot_data.setup_bokeh_server(doc)

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

