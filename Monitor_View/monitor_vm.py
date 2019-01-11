from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from . import monitor_view
import logging
import rti_python.Utilities.logger as RtiLogging


class MonitorVM(monitor_view.Ui_Monitor, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    # Create signal for value changed
    increment_value = pyqtSignal(int)

    def __init__(self, parent):
        monitor_view.Ui_Monitor.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        # Setup the logging
        RtiLogging.RtiLogger()

        self.ens_count = 0
        self.increment_value.connect(self.increment_progress)       # Connect signal and slot

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        self.ens_count = 0
        self.progressBar.setValue(0)
        self.numEnsLabel.setText("0")

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Shutdown VM")
        self.disconnect_serial()

        if self.serial_recorder:
            self.serial_recorder.close()

    @pyqtSlot(int)
    def increment_progress(self, max_count):
        """
        Update the GUI on another thread.
        :param max_count:
        :return:
        """
        self.ens_count += 1
        percentage = (self.ens_count / max_count) * 100
        self.numEnsLabel.setText(str(self.ens_count))
        self.progressBar.setValue(percentage)

