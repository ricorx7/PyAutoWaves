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
        self.verticalLayout = QtWidgets.QVBoxLayout(WaveDataDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.filePathLabel = QtWidgets.QLabel(WaveDataDialog)
        self.filePathLabel.setText("")
        self.filePathLabel.setObjectName("filePathLabel")
        self.verticalLayout.addWidget(self.filePathLabel)
        self.tabWidget = QtWidgets.QTabWidget(WaveDataDialog)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.gridLayoutWidget = QtWidgets.QWidget(self.tab)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(0, 0, 371, 231))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setContentsMargins(0, 0, 0, 0)
        self.gridLayout.setObjectName("gridLayout")
        self.textBrowser = QtWidgets.QTextBrowser(self.gridLayoutWidget)
        self.textBrowser.setObjectName("textBrowser")
        self.gridLayout.addWidget(self.textBrowser, 0, 0, 1, 1)
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.verticalLayoutWidget = QtWidgets.QWidget(self.tab_2)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(0, 0, 371, 231))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.tableWidget = QtWidgets.QTableWidget(self.verticalLayoutWidget)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.verticalLayout_2.addWidget(self.tableWidget)
        self.tabWidget.addTab(self.tab_2, "")
        self.verticalLayout.addWidget(self.tabWidget)

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

