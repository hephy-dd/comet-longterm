from PyQt5 import QtCore, QtGui, QtWidgets, QtChart

from comet import UiLoaderMixin
from comet import Device, DeviceMixin
from comet import ProcessMixin

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
        self.ui.controlsWidget.ui.ivEndSpinBox.valueChanged.connect(self.onUpdateEndVoltage)

    def loadDevices(self):
        settings = QtCore.QSettings()
        resources = settings.value('resources', {})
        self.devices().add('smu', Device(resources.get('smu', 'TCPIP::10.0.0.3::10002::SOCKET')))
        self.devices().add('multi', Device(resources.get('multi', 'TCPIP::10.0.0.3::10001::SOCKET')))
        self.devices().add('cts', Device(resources.get('cts', 'TCPIP::192.168.100.205::1080::SOCKET')))

    def createCharts(self):
        sensors = self.ui.sensorsWidget.sensors

        self.ivChart = IVChart(sensors)
        self.ui.ivChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.ivChartView.setChart(self.ivChart)

        self.itChart = ItChart(sensors)
        self.ui.ivChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.itChartView.setChart(self.itChart)

        self.ctsChart = CtsChart()
        self.ui.ctsChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
        self.ui.ctsChartView.setChart(self.ctsChart)

        self.pt100Chart = Pt100Chart(sensors)
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
        self.processes().add('meas', meas)

    @QtCore.pyqtSlot(object)
    def onEnvironReading(self, reading):
        print(reading)
        self.ctsChart.append(reading)
        self.ui.statusWidget.ui.lineEdit_2.setText("{:.1f} °C".format(reading.get('temp')))
        self.ui.statusWidget.ui.lineEdit_3.setText("{:.1f} %rH".format(reading.get('humid')))
        self.ui.statusWidget.ui.lineEdit_4.setText("ON" if reading.get('program') else "OFF")

    @QtCore.pyqtSlot(float)
    def onUpdateEndVoltage(self, value):
        self.processes.get('meas').endVoltage = value

    @QtCore.pyqtSlot(float)
    def onUpdateStepSize(self, value):
        self.processes.get('meas').stepSize = value

    @QtCore.pyqtSlot(float)
    def onUpdateIVInterval(self, value):
        self.processes.get('meas').ivInterval = value

    @QtCore.pyqtSlot(float)
    def onUpdateMeasInterval(self, value):
        self.processes.get('meas').measInterval = value

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.ui.topTabWidget.setCurrentIndex(0)

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.ui.topTabWidget.setCurrentIndex(1)
        self.ui.bottomTabWidget.setCurrentIndex(1)

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, readings):
        print('IV', readings)
        self.ivChart.append(readings)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, readings):
        print('It', readings)
        self.itChart.append(readings)

    @QtCore.pyqtSlot()
    def onStart(self):
        sensors = self.ui.sensorsWidget.sensors
        self.ivChart.load(sensors)
        self.itChart.load(sensors)
        meas = self.processes().get('meas')
        meas.start()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = CentralWidget()
    w.show()
    app.exec_()
