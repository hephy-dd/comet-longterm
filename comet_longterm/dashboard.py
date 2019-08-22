import time
import sys, os

from PyQt5 import QtCore, QtGui, QtWidgets, QtChart, uic

import comet
from comet import ureg
from comet.utilities import replace_ext
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

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

    def append(self, d):
        data = {}
        data['time'] = d.get('time')
        for i in range(self.count):
            data[i] = d.get('singles')[i]
        data['total'] = d.get('total')
        super().append(data)

Ui_Dashboard, DashboardBase = uic.loadUiType(replace_ext(__file__, '.ui'))

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

        self.environChart = QtChart.QChart()
        self.temperatureSeries = QtChart.QLineSeries()
        self.temperatureSeries.setName(self.tr("Temperature [°C]"))
        self.temperatureSeries.setColor(QtCore.Qt.red)
        self.environChart.addSeries(self.temperatureSeries)
        self.humiditySeries = QtChart.QLineSeries()
        self.humiditySeries.setName(self.tr("Humidity [%rH]"))
        self.humiditySeries.setColor(QtCore.Qt.blue)
        self.environChart.addSeries(self.humiditySeries)
        self.environChart.createDefaultAxes()
        self.environChart.axisX().setTitleText("Time [s]")
        self.environChart.axisX().setTickCount(2)
        self.environChart.axisY().setRange(0, 180)
        self.environChart.axisY().setTitleText("Temp.[°C]/Humid.[%rH]")
        self.environChart.legend().setAlignment(QtCore.Qt.AlignBottom)
        self.environChart.legend().hide()
        self.environChart.setMargins(QtCore.QMargins(2, 2, 2, 2))
        self.ui.environChartView.setChart(self.environChart)

        self.samplesChart = QtChart.QChart()
        self.samplesChart.setTitle(self.tr("Longterm"))
        self.samplesSeries = []
        for sample in self.samples:
            series = QtChart.QLineSeries()
            series.setName(format(sample.name))
            series.setColor(QtGui.QColor(*sample.color))
            self.samplesChart.addSeries(series)
            self.samplesSeries.append(series)
        self.totalSeries = QtChart.QLineSeries()
        self.totalSeries.setName(self.tr("Total bias [uA]"))
        self.totalSeries.setColor(QtGui.QColor(30, 30, 30))
        self.samplesChart.addSeries(self.totalSeries)
        self.samplesChart.createDefaultAxes()
        self.samplesChart.axisX().setTitleText("Time [s]")
        self.samplesChart.axisY().setRange(0, 80)
        self.samplesChart.axisY().setTitleText("Current [uA]")
        self.samplesChart.legend().setAlignment(QtCore.Qt.AlignRight)
        self.samplesChart.setMargins(QtCore.QMargins(2, 2, 2, 2))
        self.ui.samplesChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.samplesChartView.setChart(self.samplesChart)

        # Create environmental buffer
        self.environBuffer = comet.Buffer()
        self.environBuffer.addChannel('time')
        self.environBuffer.addChannel('temp')
        self.environBuffer.addChannel('humid')
        self.environBuffer.dataChanged.connect(self.updateEnvironChart)

        # Create environmental and worker
        self.environWorker = EnvironmentWorker(self, interval=2.5)
        self.environWorker.reading.connect(self.environBuffer.append)
        self.environWorker.reading.connect(self.setEnvironDisplay)
        self.environWorker.ready.connect(self.setReady)
        self.parent().startWorker(self.environWorker)

        self.ivBuffer = IVBuffer(len(self.samples))
        self.ivBuffer.dataChanged.connect(self.updateSamplesChart)
        self.ivBuffer.cleared.connect(self.clearSamplesChart)

        # Create measurement worker
        devices = comet.Settings().devices()
        visaLibrary = comet.Settings().visaLibrary()

        self.smu = K2410(devices.get('smu'), visaLibrary)
        self.smu.open()
        self.multi = K2700(devices.get('multi'), visaLibrary)
        self.multi.open()

        self.worker = MeasurementWorker(self.samples, self.smu, self.multi, self)
        self.worker.reading.connect(self.ivBuffer.append)
        self.worker.clear.connect(self.ivBuffer.clear)

        # Setup total bias display
        totalBias = 0. * ureg.uA
        self.ui.totalBiasValueLabel.setText("{:.3f~}".format(totalBias))

    def updateEnvironChart(self):
        data = self.environBuffer.data()
        if data.get('time'):
            self.temperatureSeries.append(QtCore.QPointF(data.get('time')[-1], data.get('temp')[-1]))
            self.humiditySeries.append(QtCore.QPointF(data.get('time')[-1], data.get('humid')[-1]))
            # Adjust range if not zoomed
            if not self.environChart.isZoomed():
                self.environChart.axisX().setRange(data.get('time')[0], data.get('time')[-1])

    def setOperator(self, index):
        settings = comet.Settings()
        settings.setCurrentOperator(index)

    def setEnvironDisplay(self, data):
        # Update display
        self.ui.tempValueLabel.setText('{:.1f} °C'.format(data.get('temp')))
        self.ui.humidValueLabel.setText('{:.1f} %rH'.format(data.get('humid')))
        self.worker.setEnvironment(data.get('temp'), data.get('humid'))

    def updateSamplesChart(self):
        data = self.ivBuffer.data()
        if data.get('time'):
            self.totalSeries.append(QtCore.QPointF(data.get('time')[-1], comet.ureg.Quantity(data.get('total')[-1], comet.ureg.A).to(comet.ureg.uA).m))
            for i, sample in enumerate(self.samples):
                self.samplesSeries[i].setVisible(sample.enabled)
                self.samplesSeries[i].append(QtCore.QPointF(data.get('time')[-1], comet.ureg.Quantity(data.get(i)[-1], comet.ureg.A).to(comet.ureg.uA).m))
            self.samplesChart.axisX().setRange(data.get('time')[0], data.get('time')[-1])
            self.samplesChart.axisY().setRange(0, self.ui.totalComplianceSpinBox.value().m * 1.2) # top up 20%

    def clearSamplesChart(self):
        self.totalSeries.clear()
        for i, sample in enumerate(self.samples):
            self.samplesSeries[i].clear()

    def selectOutputDir(self):
        """Select output directory using a file dialog."""
        path = self.ui.outputComboBox.currentText() or os.path.expanduser("~")
        path = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"), path)
        if path:
            self.ui.outputComboBox.setCurrentText(path)

    def setReady(self):
        self.ui.startButton.setEnabled(True)

    def onStart(self):
        if not self.environWorker.isGood():
            self.parent().showException("Environment worker not running!")
            return

        if self.worker.isGood():
            self.parent().showException("Measurement worker still active!")
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
