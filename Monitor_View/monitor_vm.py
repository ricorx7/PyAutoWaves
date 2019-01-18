from PyQt5.QtWidgets import QWidget, QFileSystemModel
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5 import QtGui, QtWidgets, QtCore
from . import monitor_view
from . import wavedata_vm
import logging
from rti_python.Utilities.config import RtiConfig

class MonitorVM(monitor_view.Ui_Monitor, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    # Create signal for value changed
    increment_value = pyqtSignal(int)
    reset_progress_sig = pyqtSignal()
    set_file_path_sig = pyqtSignal(str)

    def __init__(self, parent, rti_config):
        monitor_view.Ui_Monitor.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        self.rti_config = rti_config
        self.rti_config.init_waves_config()
        self.file_system_model = QFileSystemModel()
        self.ens_count = 0

        self.increment_value.connect(self.increment_progress)       # Connect signal and slot
        self.reset_progress_sig.connect(self.reset_progress)        # Connect signal and slot
        self.set_file_path_sig.connect(self.set_file_tree_path)     # Signal when output folder path changed
        self.waveFileTreeView.doubleClicked.connect(self.wave_file_selected) # Connect when tree view item double clicked

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        self.ens_count = 0
        self.progressBar.setValue(0)
        self.numEnsLabel.setText("0")
        self.file_system_model.setRootPath(self.rti_config.config['Waves']['output_dir'])
        self.waveFileTreeView.setModel(self.file_system_model)
        self.set_file_path_sig.emit(self.rti_config.config['Waves']['output_dir'])

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


    @pyqtSlot()
    def reset_progress(self):
        self.ens_count = 0
        self.numEnsLabel.setText("0")
        self.progressBar.setValue(0)

    @pyqtSlot(str)
    def set_file_tree_path(self, folder_path):
        self.waveFileTreeView.setRootIndex(self.file_system_model.setRootPath(folder_path))

    def wave_file_selected(self, index):
        item = self.waveFileTreeView.selectedIndexes()[0]
        logging.warning("Selected Index in wave data tree: " + item.model().filePath(index))
        self.open_dialog(item.model().filePath(index))

    def open_dialog(self, file_path):
        wave_data_dialog = wavedata_vm.WaveDataVM(self.parent, file_path)
        docked_wave_data_dialog = QtWidgets.QDockWidget("Waves Data: " + file_path, self)
        docked_wave_data_dialog.setAllowedAreas(QtCore.Qt.AllDockWidgetAreas)
        docked_wave_data_dialog.setFeatures(QtWidgets.QDockWidget.DockWidgetFloatable | QtWidgets.QDockWidget.DockWidgetMovable | QtWidgets.QDockWidget.DockWidgetClosable)
        docked_wave_data_dialog.setWidget(wave_data_dialog)
        self.parent.addDockWidget(QtCore.Qt.BottomDockWidgetArea, docked_wave_data_dialog)

        # Make it float when opened
        docked_wave_data_dialog.setFloating(True)
        docked_wave_data_dialog.resize(400, 300)

