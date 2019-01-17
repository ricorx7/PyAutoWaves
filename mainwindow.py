import sys
from PyQt5 import QtGui, QtWidgets, QtCore
from Setup_View.setup_vm import SetupVM
from Terminal_View.terminal_vm import TerminalVM
from Monitor_View.monitor_vm import MonitorVM
import rti_python.Utilities.logger as RtiLogging
import logging
import autowaves_manger
# import qdarkstyle
# import images_qr
from rti_python.Utilities.config import RtiConfig


class MainWindow(QtWidgets.QMainWindow):
    """
    Main window for the application
    """

    def __init__(self, config=None):
        QtWidgets.QMainWindow.__init__(self)

        # Setup the logging
        RtiLogging.RtiLogger(log_level=logging.WARNING)

        self.rti_config = RtiConfig()

        # Initialize Monitor
        self.Monitor = MonitorVM(self, self.rti_config)
        docked_monitor = QtWidgets.QDockWidget("Monitor", self)
        docked_monitor.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_monitor.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        docked_monitor.setWidget(self.Monitor)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, docked_monitor)

        # Initialize the Setup
        self.Setup = SetupVM(self, self.rti_config)
        docked_setup = QtWidgets.QDockWidget("Setup", self)
        docked_setup.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_setup.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        docked_setup.setWidget(self.Setup)
        self.addDockWidget(QtCore.Qt.TopDockWidgetArea, docked_setup)

        # Initialize Terminal
        self.Terminal = TerminalVM(self, self.rti_config)
        docked_terminal = QtWidgets.QDockWidget("Terminal", self)
        docked_terminal.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_terminal.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable)
        docked_terminal.setWidget(self.Terminal)
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, docked_terminal)

        # Add the displays to the manager to monitor all the data
        self.AutoWavesManager = autowaves_manger.AutoWavesManager(self.Terminal, self.Setup, self.Monitor)

        # Initialize the window
        self.main_window_init()

    def main_window_init(self):
        # Set the title of the window
        self.setWindowTitle("RoweTech Inc. - AutoWaves Monitor")

        self.setWindowIcon(QtGui.QIcon(":rti.ico"))

        self.resize(830, 530)

        # Show the main window
        self.show()

    def closeEvent(self, event):
        """
        Generate 'question' dialog on clicking 'X' button in title bar.

        Reimplement the closeEvent() event handler to include a 'Question'
        dialog with options on how to proceed - Close, Cancel buttons
        """
        reply = QtWidgets.QMessageBox.question(self, "Message",
            "Are you sure you want to quit?", QtWidgets.QMessageBox.Close | QtWidgets.QMessageBox.Cancel)

        if reply == QtWidgets.QMessageBox.Close:
            self.Setup.shutdown()
            self.Terminal.shutdown()
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
