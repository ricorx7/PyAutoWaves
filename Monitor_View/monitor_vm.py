from PyQt5.QtWidgets import QWidget, QFileSystemModel
from PyQt5.QtCore import pyqtSignal, pyqtSlot, QModelIndex
from PyQt5 import QtGui, QtWidgets, QtCore
from . import monitor_view
from . import wavedata_vm
import logging
import os
from rti_python.Utilities.config import RtiConfig


class MonitorVM(monitor_view.Ui_Monitor, QWidget):
    """
    Setup a view to monitor for waves data and covert it to MATLAB format for WaveForce AutoWaves.
    """

    # Create signal for value changed
    increment_burst_value = pyqtSignal(int, int)
    reset_burst_progress_sig = pyqtSignal()
    increment_avg_value = pyqtSignal(int, int)
    reset_avg_progress_sig = pyqtSignal()
    set_file_path_sig = pyqtSignal(str)
    refresh_file_tree_sig = pyqtSignal()

    def __init__(self, parent, rti_config):
        monitor_view.Ui_Monitor.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.parent = parent

        os.environ["QT_FILESYSTEMMODEL_WATCH_FILES"] = '1'                      # Automatically monitor for file changes in file tree

        self.rti_config = rti_config
        self.rti_config.init_waves_config()
        self.file_system_model = QFileSystemModel()

        self.increment_burst_value.connect(self.increment_burst_progress)       # Connect signal and slot
        self.increment_avg_value.connect(self.increment_avg_progress)           # Connect signal and slot
        self.set_file_path_sig.connect(self.set_file_tree_path)                 # Signal when output folder path changed
        self.waveFileTreeView.doubleClicked.connect(self.wave_file_selected)    # Connect when tree view item double clicked
        self.refresh_file_tree_sig.connect(self.refresh_file_tree)

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """
        self.burstProgressBar.setValue(0)
        self.burstEnsLabel.setText("0")

        self.avgProgressBar.setValue(0)
        self.avgEnsLabel.setText("0")

        self.file_system_model.setRootPath(self.rti_config.config['Waves']['output_dir'])
        self.waveFileTreeView.setModel(self.file_system_model)
        self.set_file_path_sig.emit(self.rti_config.config['Waves']['output_dir'])

        # Connect the buttons
        self.burstResetPushButton.clicked.connect(self.reset_burst_progress)
        self.avgResetPushButton.clicked.connect(self.reset_avg_progress)

    def shutdown(self):
        """
        Shutdown the VM.
        :return:
        """
        logging.debug("Shutdown VM")
        self.disconnect_serial()

        if self.serial_recorder:
            self.serial_recorder.close()

    @pyqtSlot(int, int)
    def increment_burst_progress(self, ens_count, max_count):
        """
        Update the GUI on another thread.
        :param ens_count: Current count for ensembles in the wave burst.
        :param max_count: Maximum ensembles in the wave burst
        :return:
        """
        if max_count == 0:
            max_count = 1

        if ens_count % 10 == 0 or ens_count >= max_count - 5 or ens_count <= 5:
            percentage = (ens_count / max_count) * 100
            self.burstEnsLabel.setText(str(ens_count))
            self.burstProgressBar.setValue(percentage)

    @pyqtSlot()
    def reset_burst_progress(self):
        self.burstEnsLabel.setText("0")
        self.burstProgressBar.setValue(0)

        # Need to reset the root path so the file size is updated
        self.file_system_model.setRootPath("")
        self.file_system_model.setRootPath(self.rti_config.config['Waves']['output_dir'])

        # Send a reset signal so the codec will clear the buffer
        self.reset_burst_progress_sig.emit()

    @pyqtSlot(int, int)
    def increment_avg_progress(self, count, max_count):
        """
        Update the GUI on another thread.
        :param count: Current count of ensembles in the average.
        :param max_count: Maximum ensembles in the average.
        :return:
        """
        if max_count == 0:
            max_count = 1

        if count % 10 == 0 or count >= max_count-5 or count <= 5:
            percentage = (count / max_count) * 100
            self.avgEnsLabel.setText(str(count))
            self.avgProgressBar.setValue(percentage)

    def reset_avg_progress(self):
        """
        Reset the average progress.
        :return:
        """
        self.avgEnsLabel.setText("0")
        self.avgProgressBar.setValue(0)

        # Need to reset the root path so the file size is updated
        self.file_system_model.setRootPath("")
        self.file_system_model.setRootPath(self.rti_config.config['Waves']['output_dir'])

        # Send a signal to reset average water column
        self.reset_avg_progress_sig.emit()

    def refresh_file_tree(self):
        """
        Average taken in Avereage Water Column.
        Update the file tree.
        :return:
        """
        # Need to reset the root path so the file size is updated
        self.file_system_model.setRootPath("")
        self.file_system_model.setRootPath(self.rti_config.config['Waves']['output_dir'])

    @pyqtSlot(str)
    def set_file_tree_path(self, folder_path):
        self.waveFileTreeView.setRootIndex(self.file_system_model.setRootPath(folder_path))

    def wave_file_selected(self, index):
        item = self.waveFileTreeView.selectedIndexes()[0]
        logging.debug("Selected Index in wave data tree: " + item.model().filePath(index))
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

