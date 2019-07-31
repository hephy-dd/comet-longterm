import sys, os
import time
import threading

from PyQt5 import QtCore, QtWidgets, uic
from lantz.core import ureg

from comet.qt import MainWindow
from comet.drivers.cts import ITC

class CentralWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi(os.path.join(os.path.dirname(__file__), 'main.ui'), self, 'comet.qt')
        self.rampUpEndSpinBox.setUnit(ureg.volt)
        self.rampUpStepSpinBox.setUnit(ureg.volt)
        self.rampUpDelaySpinBox.setUnit(ureg.second)
        self.biasVoltageSpinBox.setUnit(ureg.volt)
        self.totalComplianceSpinBox.setUnit(ureg.uA)
        self.singleComplianceSpinBox.setUnit(ureg.uA)
        self.timingSpinBox.setUnit(ureg.hour)
        self.timingDelaySpinBox.setUnit(ureg.second)
        settings = QtCore.QSettings()
        settings.beginGroup('preferences')
        operators = settings.value('operators', [])
        index = int(settings.value('currentOperator', 0))
        settings.endGroup()
        self.operatorComboBox.addItems(operators)
        self.operatorComboBox.setCurrentIndex(index)
        self.operatorComboBox.currentIndexChanged[int].connect(self.updateOperator)
        self.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'HPK'))

    def updateOperator(self, index):
        settings = QtCore.QSettings()
        settings.beginGroup('preferences')
        settings.setValue('currentOperator', index)
        settings.endGroup()

    def selectOutputDir(self):
        path = self.outputComboBox.currentText() or os.path.expanduser("~")
        path = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"), path)
        if path:
            self.outputComboBox.setCurrentText(path)

    def onStart(self):
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.operatorComboBox.setEnabled(False)

    def onStop(self):
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.operatorComboBox.setEnabled(True)

def main():
    app = QtWidgets.QApplication(sys.argv)

    app.setOrganizationName('HEPHY')
    app.setOrganizationDomain('hephy.at');
    app.setApplicationName('CometLongterm');

    QtCore.QSettings()

    w = MainWindow()
    w.setCentralWidget(CentralWidget(w))
    w.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)

    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
