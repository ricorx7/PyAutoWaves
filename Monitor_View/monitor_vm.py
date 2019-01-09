from PyQt5.QtWidgets import QWidget
from . import monitor_view
import logging
import rti_python.Utilities.logger as RtiLogging


class MonitorVM(monitor_view.Ui_Monitor, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    def __init__(self, parent):
        monitor_view.Ui_Monitor.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        # Setup the logging
        RtiLogging.RtiLogger()

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        self.progressBar.setValue(0)

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Shutdown VM")
        self.disconnect_serial()

        if self.serial_recorder:
            self.serial_recorder.close()

