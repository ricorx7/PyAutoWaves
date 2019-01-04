from PyQt5.QtWidgets import QWidget
from . import setup_view
import logging
import rti_python.Utilities.logger as RtiLogging


class SetupVM(setup_view.Ui_Setup, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    def __init__(self, parent):
        setup_view.Ui_Setup.__init__(self)
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

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Setup Shutdown VM")

