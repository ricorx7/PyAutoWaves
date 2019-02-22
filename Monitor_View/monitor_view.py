# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'monitor_view.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
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
        self.numEnsLabel = QtWidgets.QLabel(Monitor)
        self.numEnsLabel.setObjectName("numEnsLabel")
        self.horizontalLayout_2.addWidget(self.numEnsLabel)
        self.progressBar = QtWidgets.QProgressBar(Monitor)
        self.progressBar.setProperty("value", 24)
        self.progressBar.setObjectName("progressBar")
        self.horizontalLayout_2.addWidget(self.progressBar)
        self.verticalLayout_2.addLayout(self.horizontalLayout_2)
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
        self.label_2.setText(_translate("Monitor", "Ensemble Count: "))
        self.numEnsLabel.setText(_translate("Monitor", "23"))
        self.label.setText(_translate("Monitor", "Wave Files"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Monitor = QtWidgets.QWidget()
    ui = Ui_Monitor()
    ui.setupUi(Monitor)
    Monitor.show()
    sys.exit(app.exec_())

