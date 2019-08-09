import time
import sys, os

from PyQt5 import QtCore, QtGui, QtWidgets, uic

import comet
from comet import ureg

from .worker import *

__all__ = ['DashboardWidget']

class Function(object):

    def __init__(self):
        pass

    def __iter__(self):
        return iter(self)

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

        # Create environmental buffer
        self.environBuffer = comet.Buffer()
        self.environBuffer.addChannel('time')
        self.environBuffer.addChannel('temp')
        self.environBuffer.addChannel('humid')

        # Create environmental and worker
        self.environWorker = EnvironmentWorker(self, interval=2.5)
        self.environWorker.reading.connect(self.updateEnviron)
        self.parent().startWorker(self.environWorker)

        # Create measurement worker
        self.worker = MeasurementWorker(self)

        # Setup total bias display
        totalBias = 0. * ureg.uA
        self.ui.totalBiasLineEdit.setText("{:.3f~}".format(totalBias))

    def updateEnviron(self, reading):
        self.environBuffer.append(reading)
        comet.logger().info("environ: %s", reading)

        # How to upate pyqtgraph properly?
        data = self.environBuffer.data()
        self.tempCurve.setData(
            x=data.get('time'),
            y=data.get('temp')
        )
        self.humidCurve.setData(
            x=data.get('time'),
            y=data.get('humid')
        )

        # Update display
        self.ui.tempLineEdit.setText('{:.1f} °C'.format(reading.get('temp')))
        self.ui.humidLineEdit.setText('{:.1f} %rH'.format(reading.get('humid')))

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
        # Setup worker
        self.worker.end_voltage = self.ui.rampUpEndSpinBox.value().to(ureg.volt).m
        self.worker.step_size = self.ui.rampUpStepSpinBox.value().to(ureg.volt).m
        self.worker.step_delay = self.ui.rampUpDelaySpinBox.value().to(ureg.seconds).m
        self.worker.bias_voltage = self.ui.biasVoltageSpinBox.value().to(ureg.volt).m
        self.worker.total_compliance = self.ui.totalComplianceSpinBox.value().to(ureg.uA).m
        self.worker.single_compliance = self.ui.singleComplianceSpinBox.value().to(ureg.uA).m
        self.worker.duration = self.ui.timingDurationSpinBox.value().to(ureg.second).m
        self.worker.measurement_delay = self.ui.timingDelaySpinBox.value().to(ureg.second).m
        self.worker.finished.connect(self.onFinished)
        self.parent().startWorker(self.worker)

    def onStop(self):
        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(False)
        self.ui.operatorComboBox.setEnabled(False)
        self.worker.stop()

    def onFinished(self):
        self.ui.startButton.setEnabled(True)
        self.ui.stopButton.setEnabled(False)
        self.ui.operatorComboBox.setEnabled(True)
        self.ui.rampUpGroupBox.setEnabled(True)
        self.ui.longtermGroupBox.setEnabled(True)
