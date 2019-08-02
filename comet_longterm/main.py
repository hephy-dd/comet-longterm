import time
import threading
import sys, os
import signal

os.environ['PYVISA_LIBRARY'] = '@sim'

from PyQt5 import QtCore, QtWidgets

from comet.transport import Visa

from comet.units import ureg
from comet.worker import Worker
from comet.widgets import MainWindow
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

from ui.dashboard import Ui_Dashboard

class LongtermItWorker(Worker):

    def __init__(self):
        super().__init__()

    def run(self):
        self.setMessage("Starting measurement...")
        self.setProgress(0)
        for i in range(10):
            if not self.isGood():
                self.setProgress(0)
                self.setMessage("Measurement aborted.")
                return
            time.sleep(1)
            self.setProgress(self.progress() + 10)
        self.setProgress(100)
        self.setMessage("Done")

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

        self.ui.statusbar = self.parent().ui.statusbar
        self.ui.messageLabel = QtWidgets.QLabel(self)
        self.ui.statusbar.addWidget(self.ui.messageLabel)
        self.ui.progressBar = QtWidgets.QProgressBar(self)
        self.ui.statusbar.addWidget(self.ui.progressBar)
        self.ui.progressBar.hide()

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
        self.ui.rampUpGroupBox.setEnabled(False)
        self.ui.longtermGroupBox.setEnabled(False)
        self.ui.progressBar.show()
        # Create thread
        self.thread = QtCore.QThread()
        # Create worker
        self.worker = LongtermItWorker()
        self.worker.moveToThread(self.thread)
        # Connect worker signals
        self.worker.finished.connect(self.onFinished)
        self.worker.messageChanged.connect(self.updateMessage)
        self.worker.progressChanged.connect(self.updateProgress)
        self.worker.exceptionOccured.connect(self.exceptionOccured)
        # Connect thread signals
        self.thread.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.started.connect(self.worker.start)
        # Start thread
        self.thread.start()

    def updateMessage(self, message):
        self.ui.messageLabel.setText(message)

    def updateProgress(self, percent):
        self.ui.progressBar.setValue(percent)

    def exceptionOccured(self, exception):
        QtWidgets.QMessageBox.critical(self, "Error", format(exception))

    def onStop(self):
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(False)
        self.ui.operatorComboBox.setEnabled(False)
        self.worker.stopRequest()

    def onFinished(self):
        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.operatorComboBox.setEnabled(True)
        self.ui.rampUpGroupBox.setEnabled(True)
        self.ui.longtermGroupBox.setEnabled(True)
        self.thread.quit()
        self.thread.wait()
        self.ui.progressBar.hide()

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
