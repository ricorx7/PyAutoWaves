# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'wavedata_view.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_WaveDataDialog(object):
    def setupUi(self, WaveDataDialog):
        WaveDataDialog.setObjectName("WaveDataDialog")
        WaveDataDialog.resize(400, 300)
        self.tabWidget = QtWidgets.QTabWidget(WaveDataDialog)
        self.tabWidget.setGeometry(QtCore.QRect(10, 60, 371, 211))
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.textBrowser = QtWidgets.QTextBrowser(self.tab)
        self.textBrowser.setGeometry(QtCore.QRect(10, 0, 341, 181))
        self.textBrowser.setObjectName("textBrowser")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tableView = QtWidgets.QTableView(self.tab_2)
        self.tableView.setGeometry(QtCore.QRect(10, 0, 331, 181))
        self.tableView.setObjectName("tableView")
        self.tabWidget.addTab(self.tab_2, "")
        self.filePathLabel = QtWidgets.QLabel(WaveDataDialog)
        self.filePathLabel.setGeometry(QtCore.QRect(20, 10, 251, 16))
        self.filePathLabel.setText("")
        self.filePathLabel.setObjectName("filePathLabel")

        self.retranslateUi(WaveDataDialog)
        self.tabWidget.setCurrentIndex(0)
        QtCore.QMetaObject.connectSlotsByName(WaveDataDialog)

    def retranslateUi(self, WaveDataDialog):
        _translate = QtCore.QCoreApplication.translate
        WaveDataDialog.setWindowTitle(_translate("WaveDataDialog", "Dialog"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("WaveDataDialog", "Tab 1"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("WaveDataDialog", "Tab 2"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    WaveDataDialog = QtWidgets.QDialog()
    ui = Ui_WaveDataDialog()
    ui.setupUi(WaveDataDialog)
    WaveDataDialog.show()
    sys.exit(app.exec_())

