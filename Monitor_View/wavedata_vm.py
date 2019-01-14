from PyQt5.QtWidgets import QWidget
from Monitor_View import wavedata_view


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

        self.filePathLabel.setText(self.file_path)
