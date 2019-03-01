# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'average_water_view.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AvgWater(object):
    def setupUi(self, AvgWater):
        AvgWater.setObjectName("AvgWater")
        AvgWater.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(AvgWater)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tableWidget = QtWidgets.QTableWidget(AvgWater)
        self.tableWidget.setObjectName("tableWidget")
        self.tableWidget.setColumnCount(0)
        self.tableWidget.setRowCount(0)
        self.horizontalLayout.addWidget(self.tableWidget)

        self.retranslateUi(AvgWater)
        QtCore.QMetaObject.connectSlotsByName(AvgWater)

    def retranslateUi(self, AvgWater):
        _translate = QtCore.QCoreApplication.translate
        AvgWater.setWindowTitle(_translate("AvgWater", "Form"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AvgWater = QtWidgets.QWidget()
    ui = Ui_AvgWater()
    ui.setupUi(AvgWater)
    AvgWater.show()
    sys.exit(app.exec_())

