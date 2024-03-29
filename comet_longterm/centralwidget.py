import os
import re
import time
import datetime # TODO unify timestamp formatting!
import logging

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets
from PyQt5 import QtChart

from comet import UiLoaderMixin
from comet import Device, DeviceMixin
from comet import ProcessMixin

from comet.devices.cts import ITC
from comet.devices.keithley import K2410, K2700
from comet.devices.hephy import ShuntBox

from .logwindow import LogWindow
from .processes import EnvironProcess, MeasureProcess
from .charts import IVChart, ItChart, CtsChart, IVTempChart, ItTempChart
from .charts import ShuntBoxChart, IVSourceChart, ItSourceChart

logger = logging.getLogger(__name__)

class CentralWidget(QtWidgets.QWidget, UiLoaderMixin, DeviceMixin, ProcessMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.loadDevices()
        self.createCharts()
        self.createProcesses()

        self.logWindow = LogWindow()
        self.logWindow.addLogger(logging.getLogger())
        self.logWindow.resize(640, 420)
        self.logWindow.hide()

        self.parent().closeRequest.connect(self.onClose)
        self.controlsWidget().started.connect(self.onStart)
        self.controlsWidget().ui.ctsCheckBox.toggled.connect(self.onEnableEnviron)
        self.controlsWidget().ui.shuntBoxCheckBox.toggled.connect(self.onEnableShuntBox)
        self.statusWidget().setVoltage(None)
        self.statusWidget().setCurrent(None)
        # TODO implement measurement timer
        self.controlsWidget().ui.itDurationSpinBox.setEnabled(False)

        # Add new menu entries
        self.importCalibAction = QtWidgets.QAction(self.tr("Import &Calibrations..."))
        self.importCalibAction.triggered.connect(self.onImportCalib)
        self.parent().ui.fileMenu.insertAction(self.parent().ui.quitAction, self.importCalibAction)
        self.parent().ui.fileMenu.insertSeparator(self.parent().ui.quitAction)
        self.showLogAction = QtWidgets.QAction(self.tr("Logging..."))
        self.showLogAction.triggered.connect(self.onShowLogWindow)
        action = self.parent().ui.helpMenu.menuAction()
        menu = QtWidgets.QMenu(self.tr("&View"))
        self.parent().ui.viewMenu = self.parent().menuBar().insertMenu(action, menu).menu()
        self.parent().ui.viewMenu.addAction(self.showLogAction)

    def loadDevices(self):
        resources = QtCore.QSettings().value('resources', {})
        self.devices().add('shunt', ShuntBox(resources.get('shunt', 'TCPIP::10.0.0.2::10001::SOCKET')))
        self.devices().add('smu', K2410(resources.get('smu', 'TCPIP::10.0.0.3::10002::SOCKET')))
        self.devices().add('multi', K2700(resources.get('multi', 'TCPIP::10.0.0.3::10001::SOCKET')))
        self.devices().add('cts', ITC(resources.get('cts', 'TCPIP::192.168.100.205::1080::SOCKET')))

    def createCharts(self):
        self.ivChart = IVChart(self.sensors())
        self.ui.ivChartView.setChart(self.ivChart)
        self.itChart = ItChart(self.sensors())
        self.ui.itChartView.setChart(self.itChart)
        self.ctsChart = CtsChart()
        self.ui.ctsChartView.setChart(self.ctsChart)
        self.ivTempChart = IVTempChart(self.sensors())
        self.ui.ivTempChartView.setChart(self.ivTempChart)
        self.itTempChart = ItTempChart(self.sensors())
        self.ui.itTempChartView.setChart(self.itTempChart)
        self.shuntBoxChart = ShuntBoxChart()
        self.ui.shuntBoxChartView.setChart(self.shuntBoxChart)
        self.ivSourceChart = IVSourceChart()
        self.ui.ivSourceChartView.setChart(self.ivSourceChart)
        self.itSourceChart = ItSourceChart()
        self.ui.itSourceChartView.setChart(self.itSourceChart)

        def ivRangeChanged(minimum, maximum):
            self.ivSourceChart.fit()
            self.ivSourceChart.axisX.setRange(minimum, maximum)
            self.ivTempChart.fit()
        self.ivChart.axisX.rangeChanged.connect(ivRangeChanged)

        def itRangeChanged(minimum, maximum):
            self.itTempChart.fit()
            self.itTempChart.axisX.setRange(minimum, maximum)
            self.itSourceChart.fit()
            self.itSourceChart.axisX.setRange(minimum, maximum)
        self.itChart.axisX.rangeChanged.connect(itRangeChanged)

    def createProcesses(self):
        # Environ process
        environ = EnvironProcess(self)
        environ.reading.connect(self.onEnvironReading)
        environ.failed.connect(self.onEnvironError)
        self.processes().add('environ', environ)
        self.onEnableEnviron(self.controlsWidget().isEnvironEnabled())
        self.onEnableShuntBox(self.controlsWidget().isShuntBoxEnabled())

        # Measurement process
        meas = MeasureProcess(self)

        meas.ivStarted.connect(self.onIvStarted)
        meas.itStarted.connect(self.onItStarted)
        meas.ivReading.connect(self.onMeasIvReading)
        meas.itReading.connect(self.onMeasItReading)
        meas.smuReading.connect(self.onSmuReading)
        meas.finished.connect(self.onHalted)

        self.controlsWidget().stopRequest.connect(meas.stop)
        self.controlsWidget().useShuntBoxChanged.connect(meas.setUseShuntBox)
        self.controlsWidget().ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        self.controlsWidget().ivStepChanged.connect(meas.setIvStep)
        self.controlsWidget().ivDelayChanged.connect(meas.setIvDelay)
        self.controlsWidget().biasVoltageChanged.connect(meas.setBiasVoltage)
        self.controlsWidget().totalComplianceChanged.connect(meas.setTotalCompliance)
        self.controlsWidget().singleComplianceChanged.connect(meas.setSingleCompliance)
        self.controlsWidget().continueInComplianceChanged.connect(meas.setContinueInCompliance)
        self.controlsWidget().itDurationChanged.connect(meas.setItDuration)
        self.controlsWidget().itIntervalChanged.connect(meas.setItInterval)
        self.controlsWidget().filterEnableChanged.connect(meas.setFilterEnable)
        self.controlsWidget().filterTypeChanged.connect(meas.setFilterType)
        self.controlsWidget().filterCountChanged.connect(meas.setFilterCount)

        self.parent().connectProcess(meas)
        self.processes().add('meas', meas)

    def setLevel(self, level):
        self.logWindow.setLevel(level)

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
        self.ui.bottomTabWidget.setTabEnabled(index, enabled)
        self.statusWidget().ui.ctsGroupBox.setEnabled(enabled)
        self.statusWidget().setTemperature(float('nan'))
        self.statusWidget().setHumidity(float('nan'))
        self.statusWidget().setStatus('N/A')
        self.sensorsWidget().dataChanged() # HACK keep updated
        # Toggle environ process
        environ = self.processes().get('environ')
        environ.stop()
        environ.join()
        if enabled:
            environ.start()

    @QtCore.pyqtSlot(bool)
    def onEnableShuntBox(self, enabled):
        """Enable shunt box."""
        # Toggle pt100 tab

    @QtCore.pyqtSlot(object)
    def onEnvironReading(self, reading):
        self.ctsChart.append(reading)
        self.statusWidget().setTemperature(reading.get('temp'))
        self.statusWidget().setHumidity(reading.get('humid'))
        self.statusWidget().setStatus('{} ({})'.format(reading.get('status'), reading.get('program')))
        meas = self.processes().get('meas')
        meas.setTemperature(reading.get('temp'))
        meas.setHumidity(reading.get('humid'))
        meas.setStatus(reading.get('status'))
        meas.setProgram(reading.get('program'))
        self.sensorsWidget().dataChanged() # HACK keep updated

    @QtCore.pyqtSlot(object)
    def onEnvironError(self, exception):
        environ = self.processes().get('environ')
        # Show error only once!
        if environ.failedConnectionAttempts <= 1:
            self.parent().showException(exception)

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.ui.topTabWidget.setCurrentIndex(0)
        self.ui.bottomTabWidget.setCurrentIndex(1) # switch to IV temperature

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.ui.topTabWidget.setCurrentIndex(1)
        self.ui.bottomTabWidget.setCurrentIndex(2) # switch to It temperature

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, reading):
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get('channels')[sensor.index].get('I')
                sensor.temperature = reading.get('channels')[sensor.index].get('temp')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.ivTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.ivSourceChart.append(reading)
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, reading):
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get('channels')[sensor.index].get('I')
                sensor.temperature = reading.get('channels')[sensor.index].get('temp')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.itTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.itSourceChart.append(reading)
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
        self.ctsChart.reset()
        self.ivChart.load(self.sensors())
        self.itChart.load(self.sensors())
        self.ivTempChart.load(self.sensors())
        self.itTempChart.load(self.sensors())
        self.ivSourceChart.reset()
        self.itSourceChart.reset()

        # Setup output location
        path = os.path.normpath(self.controlsWidget().path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M-%S')
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.processes().get('meas')
        meas.setSensors(self.sensors())
        meas.setUseShuntBox(self.controlsWidget().isShuntBoxEnabled())
        meas.setIvEndVoltage(self.controlsWidget().ivEndVoltage())
        meas.setIvStep(self.controlsWidget().ivStep())
        meas.setIvDelay(self.controlsWidget().ivDelay())
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
                    logger.info("sensor[%s].resistivity = %s", i, resistors[i])
                    self.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(self, self.tr("Success"), self.tr("Sucessfully imported {} calibration resistor values.".format(count)))
            except Exception as e:
                self.parent().showException(e)

    @QtCore.pyqtSlot()
    def onShowLogWindow(self):
        self.logWindow.toBottom()
        self.logWindow.show()
        self.logWindow.raise_()

    @QtCore.pyqtSlot()
    def onClose(self):
        self.logWindow.hide()
        self.logWindow.removeLogger(logging.getLogger())
        self.sensors().storeSettings()
        self.controlsWidget().storeSettings()
