# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'average_water_view.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_AvgWater(object):
    def setupUi(self, AvgWater):
        AvgWater.setObjectName("AvgWater")
        AvgWater.resize(400, 300)
        self.horizontalLayout = QtWidgets.QHBoxLayout(AvgWater)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.tabWidget = QtWidgets.QTabWidget(AvgWater)
        self.tabWidget.setObjectName("tabWidget")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabWidget.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabWidget.addTab(self.tab_2, "")
        self.horizontalLayout.addWidget(self.tabWidget)

        self.retranslateUi(AvgWater)
        QtCore.QMetaObject.connectSlotsByName(AvgWater)

    def retranslateUi(self, AvgWater):
        _translate = QtCore.QCoreApplication.translate
        AvgWater.setWindowTitle(_translate("AvgWater", "Form"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab), _translate("AvgWater", "Tab 1"))
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.tab_2), _translate("AvgWater", "Tab 2"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    AvgWater = QtWidgets.QWidget()
    ui = Ui_AvgWater()
    ui.setupUi(AvgWater)
    AvgWater.show()
    sys.exit(app.exec_())

