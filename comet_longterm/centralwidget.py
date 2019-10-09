import os
import time, datetime

from PyQt5 import QtCore, QtGui, QtWidgets, QtChart

from comet import UiLoaderMixin
from comet import Device, DeviceMixin
from comet import ProcessMixin

from comet.devices.cts import ITC
from comet.devices.keithley import K2410, K2700

from .processes import EnvironProcess, MeasProcess
from .charts import IVChart, ItChart, CtsChart, Pt100Chart

class CentralWidget(QtWidgets.QWidget, UiLoaderMixin, DeviceMixin, ProcessMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.loadDevices()
        self.createCharts()
        self.createProcesses()

        self.ui.controlsWidget.started.connect(self.onStart)

    def loadDevices(self):
        resources = QtCore.QSettings().value('resources', {})
        self.devices().add('smu', K2410(resources.get('smu', 'TCPIP::10.0.0.3::10002::SOCKET')))
        self.devices().add('multi', K2700(resources.get('multi', 'TCPIP::10.0.0.3::10001::SOCKET')))
        self.devices().add('cts', ITC(resources.get('cts', 'TCPIP::192.168.100.205::1080::SOCKET')))

    def createCharts(self):
        self.ivChart = IVChart(self.sensors())
        self.ui.ivChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.ivChartView.setChart(self.ivChart)

        self.itChart = ItChart(self.sensors())
        self.ui.ivChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.itChartView.setChart(self.itChart)

        self.ctsChart = CtsChart()
        self.ui.ctsChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.ctsChartView.setChart(self.ctsChart)

        self.pt100Chart = Pt100Chart(self.sensors())
        self.ui.pt100ChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.pt100ChartView.setChart(self.pt100Chart)

    def createProcesses(self):
        # Environ process
        environ = EnvironProcess(self)
        environ.reading.connect(self.onEnvironReading)
        environ.start()
        self.processes().add('environ', environ)

        # Measurement process
        meas = MeasProcess(self)
        meas.ivStarted.connect(self.onIvStarted)
        meas.itStarted.connect(self.onItStarted)
        meas.ivReading.connect(self.onMeasIvReading)
        meas.itReading.connect(self.onMeasItReading)
        meas.finished.connect(self.ui.controlsWidget.onHalted)
        self.ui.controlsWidget.stopRequest.connect(meas.stop)
        self.ui.controlsWidget.ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        self.ui.controlsWidget.ivStepChanged.connect(meas.setIvStep)
        self.ui.controlsWidget.ivIntervalChanged.connect(meas.setIvInterval)
        self.ui.controlsWidget.biasVoltageChanged.connect(meas.setBiasVoltage)
        self.ui.controlsWidget.totalComplianceChanged.connect(meas.setTotalCompliance)
        self.ui.controlsWidget.singleComplianceChanged.connect(meas.setSingleCompliance)
        self.ui.controlsWidget.itDurationChanged.connect(meas.setItDuration)
        self.ui.controlsWidget.itIntervalChanged.connect(meas.setItInterval)
        self.parent().connectProcess(meas)
        self.processes().add('meas', meas)

    def sensors(self):
        """Returns sensors manager."""
        return self.ui.sensorsWidget.sensors

    @QtCore.pyqtSlot(object)
    def onEnvironReading(self, reading):
        print(reading)
        self.ctsChart.append(reading)
        self.ui.statusWidget.setTemperature(reading.get('temp'))
        self.ui.statusWidget.setHumidity(reading.get('humid'))
        self.ui.statusWidget.setProgram(reading.get('program'))
        meas = self.processes().get('meas')
        meas.setTemperature(reading.get('temp'))
        meas.setHumidity(reading.get('humid'))
        meas.setProgram(reading.get('program'))

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.ui.topTabWidget.setCurrentIndex(0)

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.ui.topTabWidget.setCurrentIndex(1)
        self.ui.bottomTabWidget.setCurrentIndex(1)

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, reading):
        self.ui.statusWidget.setVoltage(reading.get('voltage'))
        self.ui.statusWidget.setCurrent(reading.get('total'))
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, reading):
        self.ui.statusWidget.setVoltage(reading.get('voltage'))
        self.ui.statusWidget.setCurrent(reading.get('total'))
        self.itChart.append(reading)

    @QtCore.pyqtSlot()
    def onStart(self):
        self.ivChart.load(self.sensors())
        self.itChart.load(self.sensors())

        # Setup output location
        path = os.path.normpath(self.ui.controlsWidget.ui.pathComboBox.currentText())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M')
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.processes().get('meas')
        meas.setSensors(self.sensors())
        meas.setIvEndVoltage(self.ui.controlsWidget.ivEndVoltage())
        meas.setIvStep(self.ui.controlsWidget.ivStep())
        meas.setIvInterval(self.ui.controlsWidget.ivInterval())
        meas.setBiasVoltage(self.ui.controlsWidget.biasVoltage())
        meas.setTotalCompliance(self.ui.controlsWidget.totalCompliance())
        meas.setSingleCompliance(self.ui.controlsWidget.singleCompliance())
        meas.setContinueInCompliance(self.ui.controlsWidget.continueInCompliance())
        meas.setItDuration(self.ui.controlsWidget.itDuration())
        meas.setItInterval(self.ui.controlsWidget.itInterval())
        meas.setPath(path)
        meas.setOperator(self.ui.controlsWidget.operator())
        meas.start()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = CentralWidget()
    w.show()
    app.exec_()
