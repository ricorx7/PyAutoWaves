import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QAction, QFileDialog
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from Setup_View.setup_vm import SetupVM
from Terminal_View.terminal_vm import TerminalVM
from Monitor_View.monitor_vm import MonitorVM
from Average_Water_View.average_water_vm import AverageWaterVM
import logging
import rti_python.Utilities.logger as RtiLogging
RtiLogging.RtiLogger.setup_custom_logger(log_level=logging.WARNING)
import asyncio
from bokeh.server.server import Server
import autowaves_manger
# import qdarkstyle
# import images_qr
from threading import Thread
from tornado.ioloop import IOLoop
from rti_python.Utilities.config import RtiConfig


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window for the application
    """

    def __init__(self, config=None):
        QtWidgets.QMainWindow.__init__(self)

        # Setup the logging
        #RtiLogging.RtiLogger(log_level=logging.DEBUG)

        self.rti_config = RtiConfig()
        self.rti_config.init_average_waves_config()
        self.rti_config.init_terminal_config()
        self.rti_config.init_waves_config()

        # Initialize Monitor
        self.Monitor = MonitorVM(self, self.rti_config)
        docked_monitor = QtWidgets.QDockWidget("Monitor", self)
        docked_monitor.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_monitor.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        docked_monitor.setWidget(self.Monitor)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, docked_monitor)

        # Initialize the Setup
        self.Setup = SetupVM(self, self.rti_config)
        self.docked_setup = QtWidgets.QDockWidget("Setup", self)
        self.docked_setup.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_setup.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_setup.resize(500, 400)
        self.docked_setup.setWidget(self.Setup)
        self.docked_setup.setVisible(False)
        #self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, self.docked_setup)

        # Initialize Terminal
        self.Terminal = TerminalVM(self, self.rti_config)
        docked_terminal = QtWidgets.QDockWidget("Terminal", self)
        docked_terminal.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_terminal.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        docked_terminal.setWidget(self.Terminal)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, docked_terminal)
        #self.tabifyDockWidget(self.docked_setup, docked_terminal)


        # Initialize the Average Water Column
        self.AvgWater = AverageWaterVM(self, self.rti_config)
        self.docked_avg_water = QtWidgets.QDockWidget("AvgWater", self)
        self.docked_avg_water.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        self.docked_avg_water.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        self.docked_avg_water.resize(800, 600)
        self.docked_avg_water.setWidget(self.AvgWater)
        self.docked_avg_water.setVisible(False)

        # Start Event Loop needed for server
        asyncio.set_event_loop(asyncio.new_event_loop())

        # Setting num_procs here means we can't touch the IOLoop before now, we must
        # let Server handle that. If you need to explicitly handle IOLoops then you
        # will need to use the lower level BaseServer class.
        #self.server = Server({'/': self.AvgWater.setup_bokeh_server})
        apps = {'/': self.AvgWater.setup_bokeh_server}
        self.server = Server(apps, port=5001)
        self.server.start()
        self.server.show('/')

        #thread = Thread(target=self.start_bokeh_server)
        #thread.start()

        # Add the displays to the manager to monitor all the data
        self.AutoWavesManager = autowaves_manger.AutoWavesManager(self,
                                                                  self.rti_config,
                                                                  self.Terminal,
                                                                  self.Setup,
                                                                  self.Monitor,
                                                                  self.AvgWater)

        # Initialize the window
        self.main_window_init()

        # Outside the notebook ioloop needs to be started
        loop = IOLoop.current()
        #loop.start()
        t = Thread(target=loop.start, daemon=True)
        t.start()

    def main_window_init(self):
        # Set the title of the window
        self.setWindowTitle("Rowe Technologies Inc. - AutoWaves Monitor v1.1")

        self.setWindowIcon(QtGui.QIcon(":rti.ico"))

        self.resize(930, 550)

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('File')
        avgMenu = mainMenu.addMenu('Average Water')
        setupMenu = mainMenu.addMenu('Setup')

        playbackButton = QAction(QIcon('exit24.png'), 'Playback', self)
        playbackButton.setShortcut('Ctrl+P')
        playbackButton.setStatusTip('Playback files')
        playbackButton.triggered.connect(self.playback)
        fileMenu.addAction(playbackButton)

        exitButton = QAction(QIcon('exit24.png'), 'Exit', self)
        exitButton.setShortcut('Ctrl+Q')
        exitButton.setStatusTip('Exit application')
        exitButton.triggered.connect(self.close)
        fileMenu.addAction(exitButton)

        setupButton = QAction(QIcon('exit24.png'), 'Waves Setup', self)
        setupButton.setShortcut('Ctrl+S')
        setupButton.setStatusTip('Setup The Waves Settings')
        setupButton.triggered.connect(self.display_setup_view)
        setupMenu.addAction(setupButton)

        #avgWaterButton = QAction(QIcon('exit24.png'), 'Average Water', self)
        #avgWaterButton.setShortcut('Ctrl+A')
        #avgWaterButton.setStatusTip('Average the Water Column')
        #avgWaterButton.triggered.connect(self.display_avg_water_view)
        #avgMenu.addAction(avgWaterButton)

        waveHeightPlotButton = QAction(QIcon('exit24.png'), 'Water Height Plot', self)
        waveHeightPlotButton.setShortcut('Ctrl+H')
        waveHeightPlotButton.setStatusTip('Average Water Height Plot')
        waveHeightPlotButton.triggered.connect(self.display_wave_height_plot_view)
        avgMenu.addAction(waveHeightPlotButton)

        eastVelPlotButton = QAction(QIcon('exit24.png'), 'East Velocity Plot', self)
        eastVelPlotButton.setShortcut('Ctrl+E')
        eastVelPlotButton.setStatusTip('Earth Velocity [East] Plot ')
        eastVelPlotButton.triggered.connect(self.display_east_vel_plot_view)
        avgMenu.addAction(eastVelPlotButton)

        northVelPlotButton = QAction(QIcon('exit24.png'), 'North Velocity Plot', self)
        northVelPlotButton.setShortcut('Ctrl+N')
        northVelPlotButton.setStatusTip('Earth Velocity [North] Plot ')
        northVelPlotButton.triggered.connect(self.display_north_vel_plot_view)
        avgMenu.addAction(northVelPlotButton)

        magVelPlotButton = QAction(QIcon('exit24.png'), 'Velocity Magnitude Plot', self)
        magVelPlotButton.setShortcut('Ctrl+N')
        magVelPlotButton.setStatusTip('Velocity Magnitude Plot ')
        magVelPlotButton.triggered.connect(self.display_mag_plot_view)
        avgMenu.addAction(magVelPlotButton)

        dirVelPlotButton = QAction(QIcon('exit24.png'), 'Water Direction Plot', self)
        dirVelPlotButton.setShortcut('Ctrl+N')
        dirVelPlotButton.setStatusTip('Water Direction Plot ')
        dirVelPlotButton.triggered.connect(self.display_dir_plot_view)
        avgMenu.addAction(dirVelPlotButton)

        # Show the main window
        self.show()

    def start_bokeh_server(self):
        #self.server.io_loop.add_callback(self.server.show, "/")
        #self.server.io_loop.start()
        # Outside the notebook ioloop needs to be started
        loop = IOLoop.current()
        loop.start()

    def openFileNamesDialog(self):
        """
        Open a file names dialog to select multiple files.
        :return:
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(self, "Open Ensemble Files", "", "All Files (*);;Ensemble Files (*.ens)", options=options)
        return files

    @pyqtSlot()
    def display_setup_view(self):
        self.docked_setup.setFloating(True)
        self.docked_setup.show()

    @pyqtSlot()
    def display_avg_water_view(self):
        self.docked_avg_water.setFloating(True)
        self.docked_avg_water.show()

    @pyqtSlot()
    def display_wave_height_plot_view(self):
        self.AvgWater.docked_wave_height.setFloating(True)
        self.AvgWater.docked_wave_height.show()

    @pyqtSlot()
    def display_east_vel_plot_view(self):
        self.AvgWater.docked_earth_vel_east.setFloating(True)
        self.AvgWater.docked_earth_vel_east.show()

    @pyqtSlot()
    def display_north_vel_plot_view(self):
        self.AvgWater.docked_earth_vel_north.setFloating(True)
        self.AvgWater.docked_earth_vel_north.show()

    @pyqtSlot()
    def display_mag_plot_view(self):
        self.AvgWater.docked_mag.setFloating(True)
        self.AvgWater.docked_mag.show()

    @pyqtSlot()
    def display_dir_plot_view(self):
        self.AvgWater.docked_dir.setFloating(True)
        self.AvgWater.docked_dir.show()

    @pyqtSlot()
    def playback(self):
        """
        Playback files.  Select the files.  Then
        pass them to the manager to read and playback the
        files.
        :return:
        """
        # Select Files
        files = self.openFileNamesDialog()

        logging.debug("Playing back files: " + str(files))

        # Pass files to manager
        if files:
            self.AutoWavesManager.playback_file(files)

    def closeEvent(self, event):
        """
        Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Close, Cancel buttons
        """
        reply = QtWidgets.QMessageBox.question(self, "Message",
            "Are you sure you want to quit?", QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Close:
            logging.debug("Shutting down")
            self.Setup.shutdown()
            logging.debug("Setup VM shutdown")
            self.Terminal.shutdown()
            logging.debug("Terminal VL shutdown")
            self.AvgWater.shutdown()
            logging.debug("Average Water shutdown")
            self.AutoWavesManager.shutdown()
            logging.debug("Auto Waves Manager shutdown")
            event.accept()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    #app.setStyle("Mac")
    #app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())

    app.setStyle('Fusion')
    palette = QtGui.QPalette()
    palette.setColor(QtGui.QPalette.Window, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.WindowText, QtCore.Qt.white)
    #palette.setColor(QtGui.QPalette.Base, QtGui.QColor(15, 15, 15))
    palette.setColor(QtGui.QPalette.Base, QtGui.QColor(25, 25, 25))
    palette.setColor(QtGui.QPalette.AlternateBase, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.ToolTipBase, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.ToolTipText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Text, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.Dark, QtGui.QColor(35, 35, 35))
    palette.setColor(QtGui.QPalette.Shadow, QtGui.QColor(20, 20, 20))
    palette.setColor(QtGui.QPalette.Button, QtGui.QColor(53, 53, 53))
    palette.setColor(QtGui.QPalette.Link, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.ButtonText, QtCore.Qt.white)
    palette.setColor(QtGui.QPalette.BrightText, QtCore.Qt.red)
    #palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(142, 45, 197).lighter())
    palette.setColor(QtGui.QPalette.Highlight, QtGui.QColor(42, 130, 218))
    palette.setColor(QtGui.QPalette.HighlightedText, QtCore.Qt.black)
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.WindowText, QtGui.QColor(127, 127, 127))
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.ButtonText, QtGui.QColor(127, 127, 127))
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Text, QtGui.QColor(127, 127, 127))
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.Highlight, QtGui.QColor(80, 80, 80))
    palette.setColor(QtGui.QPalette.Disabled, QtGui.QPalette.HighlightedText, QtGui.QColor(127, 127, 127))

    app.setPalette(palette)


    MainWindow()
    sys.exit(app.exec_())
