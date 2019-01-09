# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'setup_view.ui'
#
# Created by: PyQt5 UI code generator 5.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets

class Ui_Setup(object):
    def setupUi(self, Setup):
        Setup.setObjectName("Setup")
        Setup.resize(404, 72)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Setup.sizePolicy().hasHeightForWidth())
        Setup.setSizePolicy(sizePolicy)
        self.formLayoutWidget = QtWidgets.QWidget(Setup)
        self.formLayoutWidget.setGeometry(QtCore.QRect(10, 10, 381, 53))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.formLayout = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.formLayout.setContentsMargins(0, 0, 0, 0)
        self.formLayout.setObjectName("formLayout")
        self.numBurstEnsLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.numBurstEnsLabel.setObjectName("numBurstEnsLabel")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.numBurstEnsLabel)
        self.numBurstEnsSpinBox = QtWidgets.QSpinBox(self.formLayoutWidget)
        self.numBurstEnsSpinBox.setMaximum(10000)
        self.numBurstEnsSpinBox.setObjectName("numBurstEnsSpinBox")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.numBurstEnsSpinBox)
        self.storagePathLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.storagePathLabel.setObjectName("storagePathLabel")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.storagePathLabel)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.storagePathLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.storagePathLineEdit.setObjectName("storagePathLineEdit")
        self.horizontalLayout_2.addWidget(self.storagePathLineEdit)
        self.selectFolderPushButton = QtWidgets.QPushButton(self.formLayoutWidget)
        self.selectFolderPushButton.setObjectName("selectFolderPushButton")
        self.horizontalLayout_2.addWidget(self.selectFolderPushButton)
        self.formLayout.setLayout(1, QtWidgets.QFormLayout.FieldRole, self.horizontalLayout_2)

        self.retranslateUi(Setup)
        QtCore.QMetaObject.connectSlotsByName(Setup)

    def retranslateUi(self, Setup):
        _translate = QtCore.QCoreApplication.translate
        Setup.setWindowTitle(_translate("Setup", "MainWindow"))
        self.numBurstEnsLabel.setText(_translate("Setup", "Number of Ensembles in Burst"))
        self.storagePathLabel.setText(_translate("Setup", "Output Directory"))
        self.selectFolderPushButton.setText(_translate("Setup", "DIR"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Setup = QtWidgets.QWidget()
    ui = Ui_Setup()
    ui.setupUi(Setup)
    Setup.show()
    sys.exit(app.exec_())

