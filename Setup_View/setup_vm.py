from PyQt5.QtWidgets import QWidget, QFileDialog
from . import setup_view
import logging
from obsub import event

class SetupVM(setup_view.Ui_Setup, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    def __init__(self, parent):
        setup_view.Ui_Setup.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

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
        self.storagePathLineEdit.textChanged.connect(self.update_settings)
        self.numBurstEnsSpinBox.valueChanged.connect(self.update_settings)

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

    def update_settings(self):
        """
        Publish the settings changed.
        :return:
        """
        self.on_waves_setting_change(self.numBurstEnsSpinBox.value(),
                                     self.storagePathLineEdit.text())

    @event
    def on_waves_setting_change(self, num_ens, file_path):
        logging.debug("Waves Settings update: " + str(num_ens) + " " + file_path)
