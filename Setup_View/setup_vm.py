from PyQt5.QtWidgets import QWidget, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from . import setup_view
import logging
from obsub import event
import os
from rti_python.Utilities.config import RtiConfig


class SetupVM(setup_view.Ui_Setup, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    folder_path_updated_sig = pyqtSignal(str)

    def __init__(self, parent):
        setup_view.Ui_Setup.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.rti_config = self.init_config()

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        self.storagePathLineEdit.setText(self.rti_config.config['Waves']['output_dir'])
        self.numBurstEnsSpinBox.setValue(self.rti_config.config['Waves'].getint('ens_in_burst'))
        self.selectFolderPushButton.clicked.connect(self.select_folder)
        self.storagePathLineEdit.setToolTip(self.storagePathLineEdit.text())
        self.storagePathLineEdit.textChanged.connect(self.update_settings)
        self.storagePathLineEdit.focusOutEvent = self.check_storage_path
        self.numBurstEnsSpinBox.valueChanged.connect(self.update_settings)

    def init_config(self):
        rti_config = RtiConfig()

        # Verify the section exist
        if not 'Waves' in rti_config.config:
            rti_config.config['Waves'] = {}
            rti_config.config['Waves']['output_dir'] = os.path.expanduser('~')
            rti_config.config['Waves']['ens_in_burst'] = '2048'

            rti_config.write()

        # Verify each value exist
        if not rti_config.config['Waves']['output_dir']:
            rti_config.config['Waves']['output_dir'] = os.path.expanduser('~')
            rti_config.write()
        if not rti_config.config['Waves']['ens_in_burst']:
            rti_config.config['Waves']['ens_in_burst'] = '2048'
            rti_config.write()

        return rti_config

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
        folder_path = QFileDialog.getExistingDirectory(self, "Select an Output Directory")

        if folder_path:
            self.storagePathLineEdit.setText(folder_path)
            self.storagePathLineEdit.setToolTip(self.storagePathLineEdit.text())
            self.folder_path_updated_sig.emit(self.storagePathLineEdit.text())      # Emit signal of folder change

    def check_storage_path(self, event):
        if not os.path.exists(self.storagePathLineEdit.text()):
            button_reply = QMessageBox.question(self, 'Directory Does Not Exist', "Output Directory does not exist.\nDo you want this directory created?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if button_reply == QMessageBox.Yes:
                os.makedirs(self.storagePathLineEdit.text())
                self.folder_path_updated_sig.emit(self.storagePathLineEdit.text())  # Emit signal of folder change
            else:
                self.storagePathLineEdit.setText(os.path.expanduser('~'))
                self.folder_path_updated_sig.emit(self.storagePathLineEdit.text())  # Emit signal of folder change
        else:
            # Folder did exist, so just emit signal that path changed
            self.folder_path_updated_sig.emit(self.storagePathLineEdit.text())  # Emit signal of folder change

        self.rti_config.config['Waves']['output_dir'] = self.storagePathLineEdit.text()
        self.rti_config.write()

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
