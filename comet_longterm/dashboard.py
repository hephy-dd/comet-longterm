import time
import sys, os

from PyQt5 import QtCore, QtGui, QtWidgets, uic

import comet
from comet import ureg

from .worker import *

__all__ = ['DashboardWidget']

N_SAMPLES = 10
"""Maximum number of samples."""

COLORS = [
    (230, 25, 75),
    (60, 180, 75),
    (255, 225, 25),
    (0, 130, 200),
    (245, 130, 48),
    (145, 30, 180),
    (70, 240, 240),
    (240, 50, 230),
    (210, 245, 60),
    (250, 190, 190),
    (0, 128, 128),
    (230, 190, 255),
    (170, 110, 40),
    (255, 250, 200),
    (128, 0, 0),
    (170, 255, 195),
    (128, 128, 0),
    (255, 215, 180),
    (0, 0, 128),
    (128, 128, 128),
    (255, 255, 255),
    (0, 0, 0),
]
"""List of distinct colors used for plots."""

class Sample(object):

    class State:
        OK = "OK"
        BAD = "BAD"

    def __init__(self, index):
        self.index = index
        self.enabled = False
        self.color = (255, 255, 255)
        self.name = ''
        self.status = self.State.OK
        self.current = 0.0
        self.temp = None

class SampleModel(QtCore.QAbstractTableModel):

    columns = ['', 'Name', 'Status', 'Current (uA)', 'PT100 Temp. (°C)']

    class Column:
        Enabled = 0
        Name = 1
        State = 2
        Current = 3
        Temp = 4

    def __init__(self, samples, parent=None):
        super().__init__(parent)
        self.samples = samples

    def rowCount(self, parent):
        return N_SAMPLES

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
            sample = self.samples[index.row()]

            if role == QtCore.Qt.DisplayRole:
                if index.column() == self.Column.Name:
                    return sample.name
                elif index.column() == self.Column.State:
                    if sample.enabled:
                        return sample.status
                elif index.column() == self.Column.Current:
                    if sample.enabled:
                        return sample.current

            elif role == QtCore.Qt.DecorationRole:
                if index.column() == self.Column.Enabled:
                    return QtGui.QColor(*sample.color)

            elif role == QtCore.Qt.ForegroundRole:
                if index.column() == self.Column.State:
                    if sample.status == sample.State.OK:
                        return QtGui.QBrush(QtCore.Qt.darkGreen)
                    return QtGui.QBrush(QtCore.Qt.darkRed)

            elif role == QtCore.Qt.CheckStateRole:
                if index.column() == self.Column.Enabled:
                    return [QtCore.Qt.Unchecked, QtCore.Qt.Checked][sample.enabled]

            elif role == QtCore.Qt.EditRole:
                if index.column() == self.Column.Name:
                    return sample.name

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            sample = self.samples[index.row()]

            if role == QtCore.Qt.CheckStateRole:
                if index.column() == self.Column.Enabled:
                    sample.enabled = value == QtCore.Qt.Checked
                    if not sample.name:
                        sample.name = self.tr("Unnamed")
                    self.dataChanged.emit(index, self.createIndex(index.row(), self.Column.Temp))
                    return True

            elif role == QtCore.Qt.EditRole:
                if index.column() == self.Column.Name:
                    sample.name = str(value)
                    self.dataChanged.emit(index, index)
                    return True
                if index.column() == self.Column.Current:
                    sample.current = value
                    self.dataChanged.emit(index, index)
                    return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == 0:
            return flags | QtCore.Qt.ItemIsUserCheckable
        if index.column() == self.Column.Name:
            return flags | QtCore.Qt.ItemIsEditable
        return flags

class IVBuffer(comet.Buffer):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.addChannel('time')
        for i in range(N_SAMPLES):
            self.addChannel(i)
        self.addChannel('total')

    def append(self, singles, total):
        data = {}
        data['time'] = time.time()
        for i in range(N_SAMPLES):
            data[i] = singles[i]
        data['total'] = total
        super().append(data)

Ui_Dashboard, DashboardBase = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dashboard.ui'))

class DashboardWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_Dashboard()
        self.ui.setupUi(self)
        self.ui.startButton.setEnabled(False)
        self.ui.rampUpEndSpinBox.setUnit(ureg.volt)
        self.ui.rampUpStepSpinBox.setUnit(ureg.volt)
        self.ui.rampUpDelaySpinBox.setUnit(ureg.second)
        self.ui.biasVoltageSpinBox.setUnit(ureg.volt)
        self.ui.totalComplianceSpinBox.setUnit(ureg.uA)
        self.ui.singleComplianceSpinBox.setUnit(ureg.uA)
        self.ui.timingDurationSpinBox.setUnit(ureg.hour)
        self.ui.timingDelaySpinBox.setUnit(ureg.second)

        settings = comet.Settings()
        self.ui.operatorComboBox.addItems(settings.operators())
        self.ui.operatorComboBox.setCurrentIndex(settings.currentOperator())
        self.ui.operatorComboBox.currentIndexChanged[int].connect(settings.setCurrentOperator)
        self.ui.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'longterm'))

        self.samples = []
        for i in range(N_SAMPLES):
            sample = Sample(i)
            sample.color = COLORS[i]
            self.samples.append(sample)
        self.model = SampleModel(self.samples, self)

        # TODO insert dummy data

        sample = self.model.samples[0]
        sample.enabled = True
        sample.name = "DUMMY1"

        sample = self.model.samples[1]
        sample.enabled = True
        sample.name = "DUMMY2"

        self.ui.samplesTableView.setModel(self.model)
        self.ui.samplesTableView.resizeColumnsToContents()
        self.ui.samplesTableView.setColumnWidth(1, 120)
        self.ui.samplesTableView.resizeRowsToContents()

        self.ui.environPlotWidget.setYRange(-40, +180)
        self.ui.environPlotWidget.plotItem.addLegend(offset=(-10,10))
        self.tempCurve = self.ui.environPlotWidget.plot(pen='r', name='temp')
        self.humidCurve = self.ui.environPlotWidget.plot(pen='b', name='humid')

        self.ui.currentPlotWidget.setYRange(0, 500)
        self.ui.currentPlotWidget.plotItem.addLegend(offset=(-0,0))
        self.singleCurves = []
        for sample in self.samples:
            curve = self.ui.currentPlotWidget.plot(pen=sample.color, name=format(sample.index))
            self.singleCurves.append(curve)
        self.totalCurve = self.ui.currentPlotWidget.plot(pen='w', name='total')

        # Create environmental buffer
        self.environBuffer = comet.Buffer()
        self.environBuffer.addChannel('time')
        self.environBuffer.addChannel('temp')
        self.environBuffer.addChannel('humid')
        self.environBuffer.dataChanged.connect(self.updateEnvironPlot)

        # Create environmental and worker
        self.environWorker = EnvironmentWorker(self, interval=2.5)
        self.environWorker.reading.connect(self.environBuffer.append)
        self.environWorker.reading.connect(self.setEnvironDisplay)
        self.environWorker.ready.connect(self.setReady)
        self.parent().startWorker(self.environWorker)

        self.ivBuffer = IVBuffer()
        self.ivBuffer.dataChanged.connect(self.updateIVPlot)

        # Create measurement worker
        self.worker = MeasurementWorker(self.samples, self.ivBuffer, self)

        # Setup total bias display
        totalBias = 0. * ureg.uA
        self.ui.totalBiasLineEdit.setText("{:.3f~}".format(totalBias))

    def updateEnvironPlot(self):
        data = self.environBuffer.data()
        self.tempCurve.setData(
            x=data.get('time'),
            y=data.get('temp')
        )
        self.humidCurve.setData(
            x=data.get('time'),
            y=data.get('humid')
        )

    def setEnvironDisplay(self, data):
        # Update display
        self.ui.tempLineEdit.setText('{:.1f} °C'.format(data.get('temp')))
        self.ui.humidLineEdit.setText('{:.1f} %rH'.format(data.get('humid')))

    def updateIVPlot(self):
        data = self.ivBuffer.data()
        self.totalCurve.setData(
            x=data.get('time'),
            y=data.get('total')
        )
        if data.get('total'):
            self.ui.totalBiasLineEdit.setText('{:.1f} uA'.format(data.get('total')[-1]))
        for i in range(10):
            self.singleCurves[i].setData(
                x=data.get('time'),
                y=data.get(i)
            )
            if data.get(i):
                self.model.setData(self.model.index(i, 3), '{:.1f} uA'.format(data.get(i)[-1]))

    def selectOutputDir(self):
        path = self.ui.outputComboBox.currentText() or os.path.expanduser("~")
        path = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"), path)
        if path:
            self.ui.outputComboBox.setCurrentText(path)

    def setReady(self):
        self.ui.startButton.setEnabled(True)

    def onStart(self):
        if not self.environWorker.isGood():
            self.parent().showException("EnvironWorker died!")
            return

        self.ui.startButton.setEnabled(False)
        self.ui.stopButton.setEnabled(True)
        self.ui.operatorComboBox.setEnabled(False)
        self.ui.rampUpGroupBox.setEnabled(False)
        self.ui.longtermGroupBox.setEnabled(False)

        # Setup output location
        path = os.path.normpath(self.ui.outputComboBox.currentText())
        if not os.path.exists(path):
            os.makedirs(path)

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
