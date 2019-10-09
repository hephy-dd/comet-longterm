import os
import re
import time
import datetime # TODO unify timestamp formatting!

from PyQt5 import QtCore, QtGui, QtWidgets, QtChart

from comet import UiLoaderMixin
from comet import Device, DeviceMixin
from comet import ProcessMixin

from comet.devices.cts import ITC
from comet.devices.keithley import K2410, K2700

from .processes import EnvironProcess, MeasProcess
from .charts import IVChart, ItChart, CtsChart, Pt100Chart
from .calibrationdialog import CalibrationDialog

class CentralWidget(QtWidgets.QWidget, UiLoaderMixin, DeviceMixin, ProcessMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.loadDevices()
        self.createCharts()
        self.createProcesses()

        self.parent().closeRequest.connect(self.onClose)
        self.ui.controlsWidget.started.connect(self.onStart)
        self.ui.controlsWidget.calibrate.connect(self.onCalibrate)

        self.ui.controlsWidget.ui.calibPushButton.setEnabled(False)
        self.importCalibAction = QtWidgets.QAction(self.tr("Import &Calibrations..."))
        self.importCalibAction.triggered.connect(self.onImportCalib)
        self.parent().ui.fileMenu.insertAction(self.parent().ui.quitAction, self.importCalibAction)
        self.parent().ui.fileMenu.insertSeparator(self.parent().ui.quitAction)

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
        self.ui.itChartView.setRubberBand(QtChart.QChartView.RectangleRubberBand)
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
        self.ui.controlsWidget.continueInComplianceChanged.connect(meas.setContinueInCompliance)
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
        for i, sensor in enumerate(self.sensors()):
            sensor.temperature = reading.get('temp')
        self.ui.sensorsWidget.dataChanged() # HACK keep updated

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
        for i, sensor in enumerate(self.sensors()):
            sensor.current = reading.get('singles')[i].get('i')
        self.ui.sensorsWidget.dataChanged() # HACK keep updated
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, reading):
        self.ui.statusWidget.setVoltage(reading.get('voltage'))
        self.ui.statusWidget.setCurrent(reading.get('total'))
        for i, sensor in enumerate(self.sensors()):
            sensor.current = reading.get('singles')[i].get('i')
        self.ui.sensorsWidget.dataChanged() # HACK keep updated
        self.itChart.append(reading)

    @QtCore.pyqtSlot()
    def onStart(self):
        self.sensors().setEditable(False)

        self.ivChart.load(self.sensors())
        self.ivChart.axisX.setRange(0, self.ui.controlsWidget.ivEndVoltage()) # V
        self.ivChart.axisY.setRange(0, self.ui.controlsWidget.singleCompliance() * 1000 * 1000) # uA
        self.itChart.load(self.sensors())
        self.itChart.axisY.setRange(0, self.ui.controlsWidget.singleCompliance() * 1000 * 1000) # uA

        # Setup output location
        path = os.path.normpath(self.ui.controlsWidget.path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M-%S')
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

    @QtCore.pyqtSlot()
    def onImportCalib(self):
        filename, filter_ = QtWidgets.QFileDialog.getOpenFileName(self,
            self.tr("Open calibration resistors file..."),
            os.path.expanduser("~")
        )
        if filename:
            # Yuck, quick'n dirty file parsing...
            try:
                resistors = []
                count = len(self.sensors())
                with open(filename) as f:
                    for token in re.findall(r'\d+\s+', f.read()):
                        print(token)
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError("Missing calibration values, expected at least {}".format(count))
                for i in range(count):
                    self.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(self, self.tr("Success"), self.tr("Sucessfully imported {} calibration resistor values.".format(count)))
            except Exception as e:
                self.parent().showException(e)


    @QtCore.pyqtSlot()
    def onCalibrate(self):
        """Show calibration dialog."""
        dialog = CalibrationDialog(self)
        dialog.exec_()
        if dialog.resistivity:
            for i, sensor in enumerate(self.sensors()):
                sensor.resistivity = dialog.resistivity[i]

    @QtCore.pyqtSlot()
    def onClose(self):
        self.sensors().storeSettings()
        self.ui.controlsWidget.storeSettings()
