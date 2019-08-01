import time
import threading
import sys, os
import signal

from PyQt5 import QtCore, QtWidgets

from slave.transport import Socket, Visa

from comet.units import ureg
from comet.widgets import MainWindow
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

from ui.dashboard import Ui_Dashboard

class DashboardWidget(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.ui.rampUpEndSpinBox.setUnit(ureg.volt)
        self.ui.rampUpStepSpinBox.setUnit(ureg.volt)
        self.ui.rampUpDelaySpinBox.setUnit(ureg.second)
        self.ui.biasVoltageSpinBox.setUnit(ureg.volt)
        self.ui.totalComplianceSpinBox.setUnit(ureg.uA)
        self.ui.singleComplianceSpinBox.setUnit(ureg.uA)
        self.ui.timingSpinBox.setUnit(ureg.hour)
        self.ui.timingDelaySpinBox.setUnit(ureg.second)
        settings = QtCore.QSettings()
        settings.beginGroup('preferences')
        operators = settings.value('operators', [])
        index = int(settings.value('currentOperator', 0))
        settings.endGroup()
        self.ui.operatorComboBox.addItems(operators)
        self.ui.operatorComboBox.setCurrentIndex(index)
        self.ui.operatorComboBox.currentIndexChanged[int].connect(self.updateOperator)
        self.ui.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'HPK'))

    def updateOperator(self, index):
        settings = QtCore.QSettings()
        settings.beginGroup('preferences')
        settings.setValue('currentOperator', index)
        settings.endGroup()

    def selectOutputDir(self):
        path = self.ui.outputComboBox.currentText() or os.path.expanduser("~")
        path = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"), path)
        if path:
            self.ui.outputComboBox.setCurrentText(path)

    def onStart(self):
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.operatorComboBox.setEnabled(False)

        try:
            with K2700(Visa('TCPIP::10.0.0.3::10002::SOCKET')) as multi:
                print(multi.idn)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", format(e))

    def onStop(self):
        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.operatorComboBox.setEnabled(True)

def main():
    app = QtWidgets.QApplication(sys.argv)

    app.setOrganizationName('HEPHY')
    app.setOrganizationDomain('hephy.at');
    app.setApplicationName('CometLongterm');

    QtCore.QSettings()

    w = MainWindow()
    w.setCentralWidget(DashboardWidget(w))
    w.show()

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)

    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
