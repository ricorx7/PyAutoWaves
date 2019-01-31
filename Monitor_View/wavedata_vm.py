from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from Monitor_View import wavedata_view
import scipy.io as sio


class WaveDataVM(wavedata_view.Ui_WaveDataDialog, QWidget):
    """
    Dialog to view the wave data.
    """

    def __init__(self, parent, file_path):
        wavedata_view.Ui_WaveDataDialog.__init__(self)
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.setWindowTitle("Waves Data:" + file_path)
        self.parent = parent

        self.file_path = file_path

        self.init_display()

    def init_display(self):
        """
        Initialize the display.
        :return:
        """

        self.resize(700, 650)

        # Set the file path of the MATLAB file
        self.filePathLabel.setText(self.file_path)

        # Read in the MATLAB file
        mat_data = sio.loadmat(self.file_path)

        self.txtLabel.setText(str(mat_data['txt'][0]))
        self.latLabel.setText(str(mat_data['lat'][0][0]))
        self.lonLabel.setText(str(mat_data['lon'][0][0]))

        # Display the MATLAB as a string
        self.textBrowser.setText(str(mat_data) + str(sio.whosmat(self.file_path)))

        # wts
        self.wtsTableWidget.setRowCount(len(mat_data['wts']))
        self.wtsTableWidget.setColumnCount(1)
        self.wtsTableWidget.setHorizontalHeaderLabels(['wts'])
        index = 0
        for col_data in mat_data['wts']:
            self.wtsTableWidget.setItem(index, 0, QTableWidgetItem(str(col_data[0])))
            index += 1

        # wb0
        self.wb0TableWidget.setRowCount(len(mat_data['wb0']))
        self.wb0TableWidget.setColumnCount(3)
        self.wb0TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb0']:
            for bin in range(len(col_data)):
                self.wb0TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
                print(str(col_data[bin]))
            index += 1

        # wb1
        self.wb1TableWidget.setRowCount(len(mat_data['wb1']))
        self.wb1TableWidget.setColumnCount(3)
        self.wb1TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb1']:
            for bin in range(len(col_data)):
                self.wb1TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
                print(str(col_data[bin]))
            index += 1

        # wb2
        self.wb2TableWidget.setRowCount(len(mat_data['wb2']))
        self.wb2TableWidget.setColumnCount(3)
        self.wb2TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb2']:
            for bin in range(len(col_data)):
                self.wb2TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
                print(str(col_data[bin]))
            index += 1

        # wb3
        self.wb3TableWidget.setRowCount(len(mat_data['wb3']))
        self.wb3TableWidget.setColumnCount(3)
        self.wb3TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb3']:
            for bin in range(len(col_data)):
                self.wb3TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
                print(str(col_data[bin]))
            index += 1


