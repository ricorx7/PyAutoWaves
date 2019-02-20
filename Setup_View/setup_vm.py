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

    def __init__(self, parent, rti_config):
        setup_view.Ui_Setup.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.rti_config = rti_config
        self.rti_config.init_waves_config()

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

        bin_list = []
        bin_list.append('Disable')
        for bin_num in range(200):
            bin_list.append(str(bin_num))

        self.selectedBin1ComboBox.addItems(bin_list)
        if self.rti_config.config['Waves']['selected_bin_1'] == '-1':
            self.selectedBin1ComboBox.setCurrentText('Disable')
        else:
            self.selectedBin1ComboBox.setCurrentText(self.rti_config.config['Waves']['selected_bin_1'])
        self.selectedBin1ComboBox.currentTextChanged.connect(self.update_settings)

        self.selectedBin2ComboBox.addItems(bin_list)
        if self.rti_config.config['Waves']['selected_bin_2'] == '-1':
            self.selectedBin2ComboBox.setCurrentText('Disable')
        else:
            self.selectedBin2ComboBox.setCurrentText(self.rti_config.config['Waves']['selected_bin_2'])
        self.selectedBin2ComboBox.currentTextChanged.connect(self.update_settings)

        self.selectedBin3ComboBox.addItems(bin_list)
        self.selectedBin3ComboBox.setCurrentText(self.rti_config.config['Waves']['selected_bin_3'])
        self.selectedBin3ComboBox.currentTextChanged.connect(self.update_settings)

        self.heightSourceComboBox.addItem('Vertical')
        self.heightSourceComboBox.addItem('Pressure')
        self.heightSourceComboBox.addItem('Beam 0')
        self.heightSourceComboBox.addItem('Beam 1')
        self.heightSourceComboBox.addItem('Beam 2')
        self.heightSourceComboBox.addItem('Beam 3')
        self.heightSourceComboBox.setCurrentText(self.rti_config.config['Waves']['height_source'])
        self.heightSourceComboBox.currentTextChanged.connect(self.update_settings)

        self.corelationThresholdDoubleSpinBox.setValue(float(self.rti_config.config['Waves']['corr_thresh']))
        self.corelationThresholdDoubleSpinBox.setToolTip("Correlation Threshold")
        self.corelationThresholdDoubleSpinBox.valueChanged.connect(self.update_settings)

        self.pressureSensorHeightDoubleSpinBox.setValue(float(self.rti_config.config['Waves']['pressure_sensor_height']))
        self.pressureSensorHeightDoubleSpinBox.setToolTip("Pressure Sensor Height above the surface of the ground in meters.")
        self.pressureSensorHeightDoubleSpinBox.valueChanged.connect(self.update_settings)

        self.pressureSensorOffsetDoubleSpinBox.setValue(float(self.rti_config.config['Waves']['pressure_sensor_offset']))
        self.pressureSensorOffsetDoubleSpinBox.setToolTip("Pressure Sensor Height offset in meters.")
        self.pressureSensorOffsetDoubleSpinBox.valueChanged.connect(self.update_settings)

        self.latitudeDoubleSpinBox.setValue(float(self.rti_config.config['Waves']['latitude']))
        self.latitudeDoubleSpinBox.setToolTip("Latitude location where the data was collected.")
        self.latitudeDoubleSpinBox.valueChanged.connect(self.update_settings)

        self.longitudeDoubleSpinBox.setValue(float(self.rti_config.config['Waves']['longitude']))
        self.longitudeDoubleSpinBox.setToolTip("Longitude location where the data was collected.")
        self.longitudeDoubleSpinBox.valueChanged.connect(self.update_settings)

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
        self.rti_config.config['Waves']['output_dir'] = self.storagePathLineEdit.text()
        self.rti_config.config['Waves']['ens_in_burst'] = str(self.numBurstEnsSpinBox.value())
        self.rti_config.config['Waves']['selected_bin_1'] = self.selectedBin1ComboBox.currentText()
        self.rti_config.config['Waves']['selected_bin_2'] = self.selectedBin2ComboBox.currentText()
        self.rti_config.config['Waves']['selected_bin_3'] = self.selectedBin3ComboBox.currentText()
        self.rti_config.config['Waves']['height_source'] = self.heightSourceComboBox.currentText()
        self.rti_config.config['Waves']['corr_thresh'] = str(self.corelationThresholdDoubleSpinBox.value())
        self.rti_config.config['Waves']['pressure_sensor_height'] = str(self.pressureSensorHeightDoubleSpinBox.value())
        self.rti_config.config['Waves']['pressure_sensor_offset'] = str(self.pressureSensorOffsetDoubleSpinBox.value())
        self.rti_config.config['Waves']['latitude'] = str(self.latitudeDoubleSpinBox.value())
        self.rti_config.config['Waves']['longitude'] = str(self.longitudeDoubleSpinBox.value())
        self.rti_config.write()

        # Verify the selected bin is not disabled
        selected_bin_1 = -1
        if self.rti_config.config['Waves']['selected_bin_1'] != 'Disable':
            selected_bin_1 = int(self.rti_config.config['Waves']['selected_bin_1'])

        selected_bin_2 = -1
        if self.rti_config.config['Waves']['selected_bin_2'] != 'Disable':
            selected_bin_2 = int(self.rti_config.config['Waves']['selected_bin_2'])

        selected_bin_3 = -1
        if self.rti_config.config['Waves']['selected_bin_3'] != 'Disable':
            selected_bin_3 = int(self.rti_config.config['Waves']['selected_bin_3'])

        height_source = 4
        if self.rti_config.config['Waves']['height_source'] == 'Beam 0':
            height_source = 0
        if self.rti_config.config['Waves']['height_source'] == 'Beam 1':
            height_source = 1
        if self.rti_config.config['Waves']['height_source'] == 'Beam 2':
            height_source = 2
        if self.rti_config.config['Waves']['height_source'] == 'Beam 3':
            height_source = 3
        if self.rti_config.config['Waves']['height_source'] == 'Vertical':
            height_source = 4
        if self.rti_config.config['Waves']['height_source'] == 'Pressure':
            height_source = 5

        # Update waves settings
        self.on_waves_setting_change(self.numBurstEnsSpinBox.value(),
                                     self.storagePathLineEdit.text(),
                                     self.latitudeDoubleSpinBox.value(),
                                     self.longitudeDoubleSpinBox.value(),
                                     selected_bin_1,
                                     selected_bin_2,
                                     selected_bin_3,
                                     self.pressureSensorHeightDoubleSpinBox.value(),
                                     height_source,
                                     self.corelationThresholdDoubleSpinBox.value(),
                                     self.pressureSensorOffsetDoubleSpinBox.value())


    @event
    def on_waves_setting_change(self, num_ens, file_path, lat, lon, bin1, bin2, bin3, ps_depth, height_source, corr_thresh, pressure_offset):
        logging.debug("Waves Settings update: " + str(num_ens) + " " + file_path)
