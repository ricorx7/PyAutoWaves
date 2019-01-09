from PyQt5.QtWidgets import QWidget, QFileDialog
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
        self.storagePathLineEdit.setText("C:\RTI_Capture")
        self.numBurstEnsSpinBox.setValue(2048)
        self.selectFolderPushButton.clicked.connect(self.select_folder)
        self.storagePathLineEdit.setToolTip(self.storagePathLineEdit.text())

    def get_storage_path(self):
        """
        :return: The storage path to record the data.
        """
        return self.storagePathLineEdit.text()

    def get_num_ens_per_burst(self):
        """
        :return: Number of ensembles per burst.
        """
        return self.numBurstEnsSpinBox.value()

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Setup Shutdown VM")

    def select_folder(self):
        """
        Open a dialog to select a folder.
        :return:
        """
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        folderPath = QFileDialog.getExistingDirectory(self, "Select an Output Directory")

        self.storagePathLineEdit.setText(folderPath)
        self.storagePathLineEdit.setToolTip(self.storagePathLineEdit.text())

