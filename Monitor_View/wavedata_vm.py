from PyQt5.QtWidgets import QWidget, QTableWidgetItem
from Monitor_View import wavedata_view
import scipy.io as sio
import datetime


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

        # Set the file path of the MATLAB file
        self.filePathLabel.setText(self.file_path)

        # Read in the MATLAB file
        mat_data = sio.loadmat(self.file_path)

        self.txtLabel.setText(str(mat_data['txt'][0]))
        self.latLabel.setText("Latitude: " + str(mat_data['lat'][0][0]))
        self.lonLabel.setText("Longitude: " + str(mat_data['lon'][0][0]))

        print(mat_data['wft'][0][0])
        print(int(mat_data['wft'][0][0]))
        print(mat_data['wft'][0][0]/100)

        st = int(mat_data['wft'][0][0])
        st += 1721059.0
        tfe = datetime.datetime.fromtimestamp(st/100).strftime('%Y-%m-%d %H:%M:%S')
        self.timeFirstEnsembleLabel.setText("Time of First Ensemble: " + tfe)
        self.timeBetweenEnsembleLabel.setText("Time Between Ensembles (sec): " + str(round(mat_data['wdt'][0][0], 2)))
        self.pressureSensorHeightLabel.setText("Pressure Sensor Height (m): " + str(mat_data['whp'][0][0]))

        # Display the MATLAB as a string
        self.textBrowser.setText(str(mat_data) + str(sio.whosmat(self.file_path)))

        # whv
        # Wave Cell Depths
        self.whvTableWidget.setRowCount(len(mat_data['whv']))
        self.whvTableWidget.setColumnCount(3)
        self.whvTableWidget.setHorizontalHeaderLabels(['Bin 1', 'Bin 2', 'Bin 3'])
        index = 0
        for col_data in mat_data['whv']:
            for bin in range(len(col_data)):
                self.whvTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wts
        # Water Temp
        self.wtsTableWidget.setRowCount(len(mat_data['wts']))
        self.wtsTableWidget.setColumnCount(1)
        self.wtsTableWidget.setHorizontalHeaderLabels(['wts'])
        index = 0
        for col_data in mat_data['wts']:
            self.wtsTableWidget.setItem(index, 0, QTableWidgetItem(str(col_data[0])))
            index += 1

        # wps
        # Pressure
        self.wpsTableWidget.setRowCount(len(mat_data['wps']))
        self.wpsTableWidget.setColumnCount(2)
        self.wpsTableWidget.setHorizontalHeaderLabels(['4 Beam', 'Vertical Beam'])
        index = 0
        for col_data in mat_data['wps']:
            self.wpsTableWidget.setItem(index, 0, QTableWidgetItem(str(col_data[0])))
            index += 1
        index = 0
        for col_data in mat_data['wzp']:
            self.wpsTableWidget.setItem(index, 1, QTableWidgetItem(str(col_data[0])))
            index += 1

        # wb0
        # Beam 0 Beam Velocity
        self.wb0TableWidget.setRowCount(len(mat_data['wb0']))
        self.wb0TableWidget.setColumnCount(3)
        self.wb0TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb0']:
            for bin in range(len(col_data)):
                self.wb0TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wb1
        # Beam 1 Beam Velocity
        self.wb1TableWidget.setRowCount(len(mat_data['wb1']))
        self.wb1TableWidget.setColumnCount(3)
        self.wb1TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb1']:
            for bin in range(len(col_data)):
                self.wb1TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wb2
        # Beam 2 Beam Velocity
        self.wb2TableWidget.setRowCount(len(mat_data['wb2']))
        self.wb2TableWidget.setColumnCount(3)
        self.wb2TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb2']:
            for bin in range(len(col_data)):
                self.wb2TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wb3
        # Beam 3 Beam Velocity
        self.wb3TableWidget.setRowCount(len(mat_data['wb3']))
        self.wb3TableWidget.setColumnCount(3)
        self.wb3TableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wb3']:
            for bin in range(len(col_data)):
                self.wb3TableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wz0
        # Vertical Beam Beam Velocity
        self.wz0TableWidget.setRowCount(len(mat_data['wz0']))
        self.wz0TableWidget.setColumnCount(1)
        self.wz0TableWidget.setHorizontalHeaderLabels(['wz0'])
        index = 0
        for col_data in mat_data['wz0']:
            self.wz0TableWidget.setItem(index, 0, QTableWidgetItem(str(col_data[0])))
            index += 1

        # wus
        # East Velocity
        self.wusTableWidget.setRowCount(len(mat_data['wus']))
        self.wusTableWidget.setColumnCount(3)
        self.wusTableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wus']:
            for bin in range(len(col_data)):
                self.wusTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wvs
        # North Velocity
        self.wvsTableWidget.setRowCount(len(mat_data['wvs']))
        self.wvsTableWidget.setColumnCount(3)
        self.wvsTableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wvs']:
            for bin in range(len(col_data)):
                self.wvsTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wzs
        # Vertical Velocity
        self.wzsTableWidget.setRowCount(len(mat_data['wzs']))
        self.wzsTableWidget.setColumnCount(3)
        self.wzsTableWidget.setHorizontalHeaderLabels(['bin 1', 'bin 2', 'bin 3'])
        index = 0
        for col_data in mat_data['wzs']:
            for bin in range(len(col_data)):
                self.wzsTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wr0,1,2,3, vertical
        # Range
        self.wr0TableWidget.setRowCount(len(mat_data['wr0']))
        self.wr0TableWidget.setColumnCount(5)
        self.wr0TableWidget.setHorizontalHeaderLabels(['Beam 0', 'Beam 1', 'Beam 2', 'Beam 3', 'Vertical Beam'])
        index = 0
        for col_data in range(len(mat_data['wr0'])):
            self.wr0TableWidget.setItem(index, 0, QTableWidgetItem(str(mat_data['wr0'][index][0])))
            self.wr0TableWidget.setItem(index, 1, QTableWidgetItem(str(mat_data['wr1'][index][0])))
            self.wr0TableWidget.setItem(index, 2, QTableWidgetItem(str(mat_data['wr2'][index][0])))
            self.wr0TableWidget.setItem(index, 3, QTableWidgetItem(str(mat_data['wr3'][index][0])))
            index += 1
        index = 0
        for col_data in mat_data['wzr']:
            self.wr0TableWidget.setItem(index, 4, QTableWidgetItem(str(col_data[0])))
            index += 1

        # whs
        # Selected Height Source Range
        self.whsTableWidget.setRowCount(len(mat_data['whs']))
        self.whsTableWidget.setColumnCount(1)
        self.whsTableWidget.setHorizontalHeaderLabels(['whs'])
        index = 0
        for col_data in mat_data['whs']:
            self.whsTableWidget.setItem(index, 0, QTableWidgetItem(str(col_data[0])))
            index += 1

        # wah
        # Average Range Tracking
        self.wahTableWidget.setRowCount(len(mat_data['wah']))
        self.wahTableWidget.setColumnCount(1)
        self.wahTableWidget.setHorizontalHeaderLabels(['Average Range'])
        index = 0
        for col_data in mat_data['wah']:
            for bin in range(len(col_data)):
                self.wahTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # whg
        # Heading
        self.whgTableWidget.setRowCount(len(mat_data['whg']))
        self.whgTableWidget.setColumnCount(1)
        self.whgTableWidget.setHorizontalHeaderLabels(['Heading'])
        index = 0
        for col_data in mat_data['whg']:
            for bin in range(len(col_data)):
                self.whgTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wph
        # Pitch
        self.wphTableWidget.setRowCount(len(mat_data['wph']))
        self.wphTableWidget.setColumnCount(1)
        self.wphTableWidget.setHorizontalHeaderLabels(['Pitch'])
        index = 0
        for col_data in mat_data['wph']:
            for bin in range(len(col_data)):
                self.wphTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1

        # wrl
        # Roll
        self.wrlTableWidget.setRowCount(len(mat_data['wrl']))
        self.wrlTableWidget.setColumnCount(1)
        self.wrlTableWidget.setHorizontalHeaderLabels(['Roll'])
        index = 0
        for col_data in mat_data['wrl']:
            for bin in range(len(col_data)):
                self.wrlTableWidget.setItem(index, bin, QTableWidgetItem(str(col_data[bin])))
            index += 1