import time
import threading
import sys, os
import signal

os.environ['PYVISA_LIBRARY'] = '@sim'

from PyQt5 import QtCore, QtWidgets

from slave.transport import Visa

from comet.units import ureg
from comet.worker import Worker
from comet.widgets import MainWindow
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

from .ui.dashboard import Ui_Dashboard

class LongtermItWorker(Worker):

    progressUnknown = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.__duration = 0

    def duration(self):
        return self.__duration

    def setDuration(self, duration):
        self.__duration = duration

    def _setup(self):
        self.setMessage("Setup instruments...")
        self.setProgress(0)
        for i in range(3):
            time.sleep(.50)
            self.setProgress(self.progress() + 100/3)
        self.setProgress(100)
        self.setMessage("Done")

    def _rampUp(self):
        self.setMessage("Ramping up...")
        self.setProgress(0)
        for i in range(10):
            if not self.isGood():
                self.setMessage("Measurement aborted.")
                return False
            time.sleep(1)
            self.setProgress(self.progress() + 100/10)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _rampBias(self):
        self.setMessage("Ramping to bias...")
        self.setProgress(0)
        for i in range(4):
            time.sleep(.25)
            self.setProgress(self.progress() + 100/4)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _longterm(self):
        self.setMessage("Longterm measurement...")
        self.setProgress(0)
        timeBegin = time.time()
        timeEnd = timeBegin + self.duration() if self.duration() else None
        if not timeEnd:
            self.progressUnknown.emit(True)
        while True:
            currentTime = time.time()
            if not self.isGood():
                self.setMessage("Measurement aborted.")
                break
            if timeEnd is not None:
                self.setProgress((currentTime-timeBegin)/(self.duration()/100.))
                if currentTime >= timeEnd:
                    break
        if not timeEnd:
            self.progressUnknown.emit(False)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _rampDown(self):
        self.setMessage("Ramping down...")
        self.setProgress(0)
        for i in range(10):
            time.sleep(.15)
            self.setProgress(self.progress() + 100/10)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def run(self):
        self.setMessage("Starting measurement...")
        self._setup()
        if self._rampUp():
            self._longterm()
        self._rampDown()
        self.setMessage("Done")

class SampleModel(QtCore.QAbstractTableModel):

    columns = ['', 'Name', 'Current (uA)', 'PT100 Temp. (deg)']

    def __init__(self, parent=None):
        super().__init__(parent)

    def rowCount(self, parent):
        return 10

    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.columns[section]
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return section

    def data(self, index, role):
        if index.isValid():
            if role == QtCore.Qt.DisplayRole:
                if index.column() == 0:
                    return QtWidgets.QCheckBox()
                else:
                    return ""
            elif role == QtCore.Qt.EditRole:
                if index.column() == 1:
                    print('XXXX')
                    return True
            elif role == QtCore.Qt.CheckStateRole:
                if index.column() == 0:
                    return QtCore.Qt.Checked

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        print('XXXX')
        if role == QtCore.Qt.EditRole:
            print('XXXX')
            row = index.row()
            column = index.column()
            if column == 1:
                if value is None:
                    value = ''
                return True
        return False

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
        self.ui.timingDurationSpinBox.setUnit(ureg.hour)
        self.ui.timingDelaySpinBox.setUnit(ureg.second)
        settings = QtCore.QSettings()
        settings.beginGroup('preferences')
        operators = settings.value('operators', [], type=list)
        index = int(settings.value('currentOperator', 0, type=int))
        settings.endGroup()
        self.ui.operatorComboBox.addItems(operators)
        self.ui.operatorComboBox.setCurrentIndex(index)
        self.ui.operatorComboBox.currentIndexChanged[int].connect(self.updateOperator)
        self.ui.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'HPK'))

        self.model = SampleModel(self)
        self.ui.samplesTableView.setModel(self.model)
        self.ui.samplesTableView.resizeColumnsToContents()
        self.ui.samplesTableView.resizeRowsToContents()

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
        self.worker.setDuration(self.ui.timingDurationSpinBox.value().to(ureg.second).m)
        self.worker.moveToThread(self.thread)
        # Connect worker signals
        self.worker.finished.connect(self.onFinished)
        self.worker.messageChanged.connect(self.updateMessage)
        self.worker.progressChanged.connect(self.updateProgress)
        self.worker.exceptionOccured.connect(self.exceptionOccured)
        self.worker.progressUnknown.connect(self.setProgressUnknown)
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

    def setProgressUnknown(self, state):
        self.ui.progressBar.setMaximum(0 if state else 100)

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
