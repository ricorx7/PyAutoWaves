# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'monitor_view.ui'
#
# Created by: PyQt5 UI code generator 5.7.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Monitor(object):
    def setupUi(self, Monitor):
        Monitor.setObjectName("Monitor")
        Monitor.resize(681, 422)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Monitor)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_2 = QtWidgets.QLabel(Monitor)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.burstEnsLabel = QtWidgets.QLabel(Monitor)
        self.burstEnsLabel.setObjectName("burstEnsLabel")
        self.horizontalLayout_2.addWidget(self.burstEnsLabel)
        self.burstProgressBar = QtWidgets.QProgressBar(Monitor)
        self.burstProgressBar.setProperty("value", 24)
        self.burstProgressBar.setObjectName("burstProgressBar")
        self.horizontalLayout_2.addWidget(self.burstProgressBar)
        self.burstResetPushButton = QtWidgets.QPushButton(Monitor)
        self.burstResetPushButton.setObjectName("burstResetPushButton")
        self.horizontalLayout_2.addWidget(self.burstResetPushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_4 = QtWidgets.QLabel(Monitor)
        self.label_4.setObjectName("label_4")
        self.horizontalLayout.addWidget(self.label_4)
        self.avgEnsLabel = QtWidgets.QLabel(Monitor)
        self.avgEnsLabel.setObjectName("avgEnsLabel")
        self.horizontalLayout.addWidget(self.avgEnsLabel)
        self.avgProgressBar = QtWidgets.QProgressBar(Monitor)
        self.avgProgressBar.setProperty("value", 24)
        self.avgProgressBar.setObjectName("avgProgressBar")
        self.horizontalLayout.addWidget(self.avgProgressBar)
        self.avgResetPushButton = QtWidgets.QPushButton(Monitor)
        self.avgResetPushButton.setObjectName("avgResetPushButton")
        self.horizontalLayout.addWidget(self.avgResetPushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.label = QtWidgets.QLabel(Monitor)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.waveFileTreeView = QtWidgets.QTreeView(Monitor)
        self.waveFileTreeView.setObjectName("waveFileTreeView")
        self.verticalLayout_2.addWidget(self.waveFileTreeView)

        self.retranslateUi(Monitor)
        QtCore.QMetaObject.connectSlotsByName(Monitor)

    def retranslateUi(self, Monitor):
        _translate = QtCore.QCoreApplication.translate
        Monitor.setWindowTitle(_translate("Monitor", "Form"))
        self.label_2.setText(_translate("Monitor", "Burst Ensemble Count:     "))
        self.burstEnsLabel.setText(_translate("Monitor", "23"))
        self.burstResetPushButton.setText(_translate("Monitor", "Reset"))
        self.label_4.setText(_translate("Monitor", "Average Ensemble Count: "))
        self.avgEnsLabel.setText(_translate("Monitor", "23"))
        self.avgResetPushButton.setText(_translate("Monitor", "Reset"))
        self.label.setText(_translate("Monitor", "Wave Files"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Monitor = QtWidgets.QWidget()
    ui = Ui_Monitor()
    ui.setupUi(Monitor)
    Monitor.show()
    sys.exit(app.exec_())

