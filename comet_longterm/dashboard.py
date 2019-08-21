import time
import sys, os

from PyQt5 import QtCore, QtGui, QtWidgets, uic

import comet
from comet import ureg

from .samples import SampleManager, SampleModel
from .worker import *

__all__ = ['DashboardWidget']

class IVBuffer(comet.Buffer):

    def __init__(self, count, parent=None):
        """Buffer for samples."""
        super().__init__(parent)
        self.count = count
        self.addChannel('time')
        for i in range(count):
            self.addChannel(i)
        self.addChannel('total')

    def append(self, singles, total):
        data = {}
        data['time'] = time.time()
        for i in range(self.count):
            data[i] = singles[i]
        data['total'] = total
        super().append(data)

Ui_Dashboard, DashboardBase = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'dashboard.ui'))

class DashboardWidget(QtWidgets.QWidget):

    MaxSamples = 10

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
        self.ui.timingDelaySpinBox.setUnit(ureg.minute)

        settings = comet.Settings()
        self.ui.operatorComboBox.addItems(settings.operators())
        self.ui.operatorComboBox.setCurrentIndex(settings.currentOperator())
        self.ui.operatorComboBox.currentIndexChanged[int].connect(self.setOperator)
        self.ui.outputComboBox.addItem(os.path.join(os.path.expanduser("~"), 'longterm'))

        self.samples = SampleManager(self.MaxSamples)
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

        self.ivBuffer = IVBuffer(len(self.samples))
        self.ivBuffer.dataChanged.connect(self.updateIVPlot)

        # Create measurement worker
        self.worker = MeasurementWorker(self.samples, self.ivBuffer, self)

        # Setup total bias display
        totalBias = 0. * ureg.uA
        self.ui.totalBiasValueLabel.setText("{:.3f~}".format(totalBias))

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

    def setOperator(self, index):
        settings = comet.Settings()
        settings.setCurrentOperator(index)

    def setEnvironDisplay(self, data):
        # Update display
        self.ui.tempValueLabel.setText('{:.1f} °C'.format(data.get('temp')))
        self.ui.humidValueLabel.setText('{:.1f} %rH'.format(data.get('humid')))

    def updateIVPlot(self):
        data = self.ivBuffer.data()
        self.totalCurve.setData(
            x=data.get('time'),
            y=data.get('total')
        )
        if data.get('total'):
            self.ui.totalBiasValueLabel.setText('{:.1f} uA'.format(data.get('total')[-1]))
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
        self.worker.total_compliance = self.ui.totalComplianceSpinBox.value().to(ureg.A).m
        self.worker.single_compliance = self.ui.singleComplianceSpinBox.value().to(ureg.A).m
        self.worker.duration = self.ui.timingDurationSpinBox.value().to(ureg.second).m
        self.worker.measurement_delay = self.ui.timingDelaySpinBox.value().to(ureg.second).m
        self.worker.path = path
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
