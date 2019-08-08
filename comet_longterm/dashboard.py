import time
import sys, os

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from slave.transport import Visa, Socket

from comet import ureg
from comet.drivers.cts import ITC

from .worker import Worker

__all__ = ['DashboardWidget']

class SampleModel(QtCore.QAbstractTableModel):

    columns = ['', 'Name', 'Status', 'Current (uA)', 'PT100 Temp. (°C)']

    status = ["OK", "BAD", "OK", "OK", "OK", "OK", "OK", "OK", "OK", "OK"]

    class Column:
        Enabled = 0
        Name = 1
        State = 2
        Current = 3
        Temp = 4

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
                return section + 1

    def data(self, index, role):
        if index.isValid():
            status = self.status[index.row()]
            if role == QtCore.Qt.DisplayRole:
                if index.column() == self.Column.Enabled:
                    return QtWidgets.QCheckBox()
                elif index.column() == self.Column.State:
                    return status
                else:
                    return ""
            elif role == QtCore.Qt.ForegroundRole:
                if index.column() == self.Column.State:
                    if status == "OK":
                        return QtGui.QBrush(QtCore.Qt.darkGreen)
                    return QtGui.QBrush(QtCore.Qt.darkRed)
            elif role == QtCore.Qt.EditRole:
                if index.column() == self.Column.Name:
                    return True
            elif role == QtCore.Qt.CheckStateRole:
                if index.column() == self.Column.Enabled:
                    return QtCore.Qt.Checked

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            row = index.row()
            column = index.column()
            if column == self.Column.Enabled:
                if value is None:
                    value = ''
                return True
        return False

Ui_Dashboard, DashboardBase = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dashboard.ui'))

class DashboardWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
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
        operators = settings.value('operators', ['Monty'], type=list)
        index = int(settings.value('currentOperator', 0, type=int))
        devices = settings.value('devices', [['cts', '192.168.100.205']], type=list)
        settings.setValue('devices', devices)
        settings.endGroup()

        self.ui.operatorComboBox.addItems(operators)
        self.ui.operatorComboBox.setCurrentIndex(index)
        self.ui.operatorComboBox.currentIndexChanged[int].connect(self.updateOperator)
        self.ui.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'longterm'))

        self.model = SampleModel(self)
        self.ui.samplesTableView.setModel(self.model)
        self.ui.samplesTableView.resizeColumnsToContents()
        self.ui.samplesTableView.resizeRowsToContents()

        self.ui.environPlotWidget.setYRange(-40, +180)
        self.ui.environPlotWidget.plotItem.addLegend(offset=(-10,10))
        self.tempCurve = self.ui.environPlotWidget.plot(pen='r', name='temp')
        self.humidCurve = self.ui.environPlotWidget.plot(pen='b', name='humid')

        self.ui.currentPlotWidget.setYRange(0, 500)
        self.ui.currentPlotWidget.plotItem.addLegend(offset=(-0,0))
        for i in range(1, 11):
            curve = self.ui.currentPlotWidget.plot(pen='g', name=format(i))

        self.__its = ITC(Socket(address=('192.168.100.205', 1080)))
        self.__environ = dict(time=[], temp=[], humid=[])

        self.__environTimer = QtCore.QTimer()
        self.__environTimer.timeout.connect(self.updateEnviron)
        self.__environTimer.start(2500)

    def updateEnviron(self):
        t = time.time()
        self.__its._transport.write(b'A0')
        temp = float(self.__its._transport.read_bytes(14).decode().split(' ')[1])
        self.__its._transport.write(b'A1')
        humid = float(self.__its._transport.read_bytes(14).decode().split(' ')[1])
        self.__environ.get('time').append(t)
        self.__environ.get('temp').append(temp)
        self.__environ.get('humid').append(humid)
        print(t, temp, humid, flush=True)
        self.tempCurve.setData(
            x=self.__environ.get('time'),
            y=self.__environ.get('temp')
        )
        self.humidCurve.setData(
            x=self.__environ.get('time'),
            y=self.__environ.get('humid')
        )
        self.ui.tempLineEdit.setText('{:.1f} °C'.format(temp))
        self.ui.humidLineEdit.setText('{:.1f} %'.format(humid))

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
        self.worker = Worker()
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
