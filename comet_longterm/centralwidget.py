import os
import re
import time
import datetime # TODO unify timestamp formatting!
import logging

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

        self.parent().closeRequest.connect(self.onClose)
        self.controlsWidget().started.connect(self.onStart)
        self.controlsWidget().ui.useCtsCheckBox.toggled.connect(self.onEnableEnviron)
        self.statusWidget().setVoltage(None)
        self.statusWidget().setCurrent(None)
        # TODO implement measurement timer
        self.controlsWidget().ui.itDurationSpinBox.setEnabled(False)

        # Add new menu entries
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
        environ.failed.connect(self.onEnvironError)
        self.processes().add('environ', environ)
        self.onEnableEnviron(self.controlsWidget().ui.useCtsCheckBox.isChecked())

        # Measurement process
        meas = MeasProcess(self)

        meas.ivStarted.connect(self.onIvStarted)
        meas.itStarted.connect(self.onItStarted)
        meas.ivReading.connect(self.onMeasIvReading)
        meas.itReading.connect(self.onMeasItReading)
        meas.smuReading.connect(self.onSmuReading)
        meas.finished.connect(self.onHalted)

        self.controlsWidget().stopRequest.connect(meas.stop)
        self.controlsWidget().ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        self.controlsWidget().ivStepChanged.connect(meas.setIvStep)
        self.controlsWidget().ivIntervalChanged.connect(meas.setIvInterval)
        self.controlsWidget().biasVoltageChanged.connect(meas.setBiasVoltage)
        self.controlsWidget().totalComplianceChanged.connect(meas.setTotalCompliance)
        self.controlsWidget().singleComplianceChanged.connect(meas.setSingleCompliance)
        self.controlsWidget().continueInComplianceChanged.connect(meas.setContinueInCompliance)
        self.controlsWidget().itDurationChanged.connect(meas.setItDuration)
        self.controlsWidget().itIntervalChanged.connect(meas.setItInterval)

        self.parent().connectProcess(meas)
        self.processes().add('meas', meas)

    def sensors(self):
        """Returns sensors manager."""
        return self.sensorsWidget().sensors

    def sensorsWidget(self):
        """Returns sensors widget."""
        return self.ui.sensorsWidget

    def controlsWidget(self):
        """Returns controls widget."""
        return self.ui.controlsWidget

    def statusWidget(self):
        """Returns status widget."""
        return self.ui.statusWidget

    @QtCore.pyqtSlot(bool)
    def onEnableEnviron(self, enabled):
        """Enable environment process."""
        # Toggle environ tab
        index = self.ui.bottomTabWidget.indexOf(self.ui.ctsTab)
        self.ui.bottomTabWidget.setTabEnabled(index, enabled);
        # Toggle environ process
        environ = self.processes().get('environ')
        environ.stop()
        environ.join()
        if enabled:
            environ.start()

    @QtCore.pyqtSlot(object)
    def onEnvironReading(self, reading):
        self.ctsChart.append(reading)
        self.statusWidget().setTemperature(reading.get('temp'))
        self.statusWidget().setHumidity(reading.get('humid'))
        self.statusWidget().setProgram(reading.get('program'))
        meas = self.processes().get('meas')
        meas.setTemperature(reading.get('temp'))
        meas.setHumidity(reading.get('humid'))
        meas.setProgram(reading.get('program'))
        for i, sensor in enumerate(self.sensors()):
            sensor.temperature = reading.get('temp')
        self.sensorsWidget().dataChanged() # HACK keep updated

    @QtCore.pyqtSlot(object)
    def onEnvironError(self, error):
        environ = self.processes().get('environ')
        # Show error only once!
        if environ.failedConnectionAttempts <= 1:
            self.parent().showException(error)

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.ui.topTabWidget.setCurrentIndex(0)

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.ui.topTabWidget.setCurrentIndex(1)
        self.ui.bottomTabWidget.setCurrentIndex(1)

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, reading):
        for i, sensor in enumerate(self.sensors()):
            sensor.current = reading.get('channels')[i].get('I')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, reading):
        for i, sensor in enumerate(self.sensors()):
            sensor.current = reading.get('channels')[i].get('I')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.itChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onSmuReading(self, reading):
        self.statusWidget().setVoltage(reading.get('U'))
        self.statusWidget().setCurrent(reading.get('I'))

    @QtCore.pyqtSlot()
    def onStart(self):
        self.sensors().setEditable(False)
        self.statusWidget().setCurrent(None)

        # TODO
        self.ivChart.load(self.sensors())
        self.ivChart.axisX.setRange(0, self.controlsWidget().ivEndVoltage()) # V
        self.ivChart.axisY.setRange(0, self.controlsWidget().singleCompliance() * 1000 * 1000) # uA
        self.itChart.load(self.sensors())
        self.itChart.axisY.setRange(0, self.controlsWidget().singleCompliance() * 1000 * 1000) # uA

        # Setup output location
        path = os.path.normpath(self.controlsWidget().path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M-%S')
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.processes().get('meas')
        meas.setSensors(self.sensors())
        meas.setIvEndVoltage(self.controlsWidget().ivEndVoltage())
        meas.setIvStep(self.controlsWidget().ivStep())
        meas.setIvInterval(self.controlsWidget().ivInterval())
        meas.setBiasVoltage(self.controlsWidget().biasVoltage())
        meas.setTotalCompliance(self.controlsWidget().totalCompliance())
        meas.setSingleCompliance(self.controlsWidget().singleCompliance())
        meas.setContinueInCompliance(self.controlsWidget().continueInCompliance())
        meas.setItDuration(self.controlsWidget().itDuration())
        meas.setItInterval(self.controlsWidget().itInterval())
        meas.setPath(path)
        meas.setOperator(self.controlsWidget().operator())

        meas.start()

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.controlsWidget().onHalted()
        self.statusWidget().setCurrent(None)
        self.statusWidget().setVoltage(None)
        self.statusWidget().setCurrent(None)
        self.sensors().setEditable(True)

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
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError("Missing calibration values, expected at least {}".format(count))
                for i in range(count):
                    logging.info("sensor[%s].resistivity = %s", i, resistors[i])
                    self.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(self, self.tr("Success"), self.tr("Sucessfully imported {} calibration resistor values.".format(count)))
            except Exception as e:
                self.parent().showException(e)

    @QtCore.pyqtSlot()
    def onClose(self):
        self.sensors().storeSettings()
        self.controlsWidget().storeSettings()
