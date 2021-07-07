import datetime
import logging
import os
import re
import time

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from comet import Application
from comet import MainWindow
from comet import DeviceMixin
from comet import ProcessMixin

from comet.devices.cts import ITC
from comet.devices.keithley import K2410
from comet.devices.keithley import K2700
from comet.devices.hephy import ShuntBox

from . import __version__
from .processes import EnvironProcess
from .processes import MeasureProcess
from .centralwidget import CentralWidget
from .logwindow import LogWindow

logger = logging.getLogger(__name__)

class Controller(QtCore.QObject, DeviceMixin, ProcessMixin):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = MainWindow()
        self.view.setCentralWidget(CentralWidget(self.view))
        self.view.setWindowTitle("{} {}".format(self.view.windowTitle(), __version__))
        self.view.setProperty('contentsUrl', 'https://github.com/hephy-dd/comet-longterm')

        self.createLogWindow()
        self.createDevices()
        self.createProcesses()

        widget = self.view.centralWidget()
        widget.controlsWidget().ui.ctsCheckBox.toggled.connect(self.onEnableEnviron)
        widget.controlsWidget().ui.shuntBoxCheckBox.toggled.connect(self.onEnableShuntBox)
        widget.controlsWidget().started.connect(self.onStart)
        widget.controlsWidget().stopRequest.connect(self.onStopRequest)
        widget.controlsWidget().halted.connect(self.onHalted)

        # Add new menu entries
        self.importCalibAction = QtWidgets.QAction(self.tr("Import &Calibrations..."))
        self.importCalibAction.triggered.connect(self.onImportCalib)

        self.view.ui.fileMenu.insertAction(self.view.ui.quitAction, self.importCalibAction)
        self.view.ui.fileMenu.insertSeparator(self.view.ui.quitAction)

        self.startAction = QtWidgets.QAction(widget.tr("Start"))
        self.startAction.triggered.connect(widget.controlsWidget().onStart)

        self.stopAction = QtWidgets.QAction(widget.tr("Stop"))
        self.stopAction.triggered.connect(widget.controlsWidget().onStop)
        self.stopAction.setEnabled(False)

        controlMenu = QtWidgets.QMenu(self.tr("&Control"))
        action = self.view.ui.helpMenu.menuAction()
        self.controlMenu = self.view.menuBar().insertMenu(action, controlMenu).menu()
        self.controlMenu.addAction(self.startAction)
        self.controlMenu.addAction(self.stopAction)

        self.showLogAction = QtWidgets.QAction(widget.tr("Logging..."))
        self.showLogAction.triggered.connect(self.onShowLogWindow)

        viewMenu = QtWidgets.QMenu(self.tr("&View"))
        action = self.view.ui.helpMenu.menuAction()
        self.viewMenu = self.view.menuBar().insertMenu(action, viewMenu).menu()
        self.viewMenu.addAction(self.showLogAction)

        self.view.closeRequest.connect(self.onClose)

    def loadSettings(self):
        settings = QtCore.QSettings()

        # Main window
        size = settings.value("mainwindow.size", QtCore.QSize(1280, 700))
        self.view.resize(size)

    def storeSettings(self):
        settings = QtCore.QSettings()

        # Main window
        settings.setValue("mainwindow.size", self.view.size())

    def eventLoop(self):
        self.view.show()
        return Application.instance().run()

    def createLogWindow(self):
        self.logWindow = LogWindow()
        self.logWindow.addLogger(logging.getLogger())
        self.logWindow.resize(640, 420)
        self.logWindow.hide()

    def createDevices(self):
        resources = QtCore.QSettings().value('resources', {})
        self.devices().add('shunt', ShuntBox(resources.get('shunt', 'TCPIP::10.0.0.2::10001::SOCKET')))
        self.devices().add('smu', K2410(resources.get('smu', 'TCPIP::10.0.0.3::10002::SOCKET')))
        self.devices().add('multi', K2700(resources.get('multi', 'TCPIP::10.0.0.3::10001::SOCKET')))
        self.devices().add('cts', ITC(resources.get('cts', 'TCPIP::192.168.100.205::1080::SOCKET')))

    def createProcesses(self):
        widget = self.view.centralWidget()
        # Environ process
        environ = EnvironProcess(self)
        environ.reading.connect(self.onEnvironReading)
        environ.failed.connect(self.onEnvironError)
        self.processes().add('environ', environ)
        self.onEnableEnviron(widget.controlsWidget().isEnvironEnabled())
        self.onEnableShuntBox(widget.controlsWidget().isShuntBoxEnabled())

        # Measurement process
        meas = MeasureProcess(self)

        meas.ivStarted.connect(widget.onIvStarted)
        meas.itStarted.connect(widget.onItStarted)
        meas.ivReading.connect(widget.onMeasIvReading)
        meas.itReading.connect(widget.onMeasItReading)
        meas.smuReading.connect(widget.onSmuReading)
        meas.finished.connect(widget.onHalted)

        widget.controlsWidget().stopRequest.connect(meas.stop)
        widget.controlsWidget().useShuntBoxChanged.connect(meas.setUseShuntBox)
        widget.controlsWidget().ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        widget.controlsWidget().ivStepChanged.connect(meas.setIvStep)
        widget.controlsWidget().ivDelayChanged.connect(meas.setIvDelay)
        widget.controlsWidget().biasVoltageChanged.connect(meas.setBiasVoltage)
        widget.controlsWidget().totalComplianceChanged.connect(meas.setTotalCompliance)
        widget.controlsWidget().singleComplianceChanged.connect(meas.setSingleCompliance)
        widget.controlsWidget().continueInComplianceChanged.connect(meas.setContinueInCompliance)
        widget.controlsWidget().itDurationChanged.connect(meas.setItDuration)
        widget.controlsWidget().itIntervalChanged.connect(meas.setItInterval)
        widget.controlsWidget().filterEnableChanged.connect(meas.setFilterEnable)
        widget.controlsWidget().filterTypeChanged.connect(meas.setFilterType)
        widget.controlsWidget().filterCountChanged.connect(meas.setFilterCount)

        widget.parent().connectProcess(meas)
        self.processes().add('meas', meas)

    def setLevel(self, level):
        self.logWindow.setLevel(level)

    @QtCore.pyqtSlot(bool)
    def onEnableEnviron(self, enabled):
        """Enable environment process."""
        widget = self.view.centralWidget()
        # Toggle environ tab
        index = widget.ui.bottomTabWidget.indexOf(widget.ui.ctsTab)
        widget.ui.bottomTabWidget.setTabEnabled(index, enabled)
        widget.statusWidget().ui.ctsGroupBox.setEnabled(enabled)
        widget.statusWidget().setTemperature(float('nan'))
        widget.statusWidget().setHumidity(float('nan'))
        widget.statusWidget().setStatus('N/A')
        widget.sensorsWidget().dataChanged() # HACK keep updated
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
        widget = self.view.centralWidget()
        widget.ctsChart.append(reading)
        widget.statusWidget().setTemperature(reading.get('temp'))
        widget.statusWidget().setHumidity(reading.get('humid'))
        widget.statusWidget().setStatus('{} ({})'.format(reading.get('status'), reading.get('program')))
        meas = self.processes().get('meas')
        meas.setTemperature(reading.get('temp'))
        meas.setHumidity(reading.get('humid'))
        meas.setStatus(reading.get('status'))
        meas.setProgram(reading.get('program'))
        widget.sensorsWidget().dataChanged() # HACK keep updated

    @QtCore.pyqtSlot(object)
    def onEnvironError(self, exc):
        environ = self.processes().get('environ')
        # Show error only once!
        if environ.failedConnectionAttempts <= 1:
            self.parent().showException(exc)

    @QtCore.pyqtSlot()
    def onStart(self):
        widget = self.view.centralWidget()
        widget.sensors().setEditable(False)
        widget.statusWidget().setCurrent(None)

        self.startAction.setEnabled(False)
        self.stopAction.setEnabled(True)

        # TODO
        widget.ctsChart.reset()
        widget.ivChart.load(widget.sensors())
        widget.itChart.load(widget.sensors())
        widget.ivTempChart.load(widget.sensors())
        widget.itTempChart.load(widget.sensors())
        widget.ivSourceChart.reset()
        widget.itSourceChart.reset()

        # Setup output location
        path = os.path.normpath(widget.controlsWidget().path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime('%Y-%m-%dT%H-%M-%S')
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.processes().get('meas')
        meas.setSensors(widget.sensors())
        meas.setUseShuntBox(widget.controlsWidget().isShuntBoxEnabled())
        meas.setIvEndVoltage(widget.controlsWidget().ivEndVoltage())
        meas.setIvStep(widget.controlsWidget().ivStep())
        meas.setIvDelay(widget.controlsWidget().ivDelay())
        meas.setBiasVoltage(widget.controlsWidget().biasVoltage())
        meas.setTotalCompliance(widget.controlsWidget().totalCompliance())
        meas.setSingleCompliance(widget.controlsWidget().singleCompliance())
        meas.setContinueInCompliance(widget.controlsWidget().continueInCompliance())
        meas.setItDuration(widget.controlsWidget().itDuration())
        meas.setItInterval(widget.controlsWidget().itInterval())
        meas.setFilterEnable(widget.controlsWidget().filterEnable())
        meas.setFilterCount(widget.controlsWidget().filterCount())
        meas.setFilterType(widget.controlsWidget().filterType())
        meas.setPath(path)
        meas.setOperator(widget.controlsWidget().operator())

        meas.start()

    @QtCore.pyqtSlot()
    def onStopRequest(self):
        self.startAction.setEnabled(False)
        self.stopAction.setEnabled(False)

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.startAction.setEnabled(True)
        self.stopAction.setEnabled(False)

    @QtCore.pyqtSlot()
    def onImportCalib(self):
        widget = self.view.centralWidget()
        filename, filter_ = QtWidgets.QFileDialog.getOpenFileName(widget,
            widget.tr("Open calibration resistors file..."),
            os.path.expanduser("~")
        )
        if filename:
            # Yuck, quick'n dirty file parsing...
            try:
                resistors = []
                count = len(widget.sensors())
                with open(filename) as f:
                    for token in re.findall(r'\d+\s+', f.read()):
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError("Missing calibration values, expected at least {}".format(count))
                for i in range(count):
                    logger.info("sensor[%s].resistivity = %s", i, resistors[i])
                    widget.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(widget, widget.tr("Success"), widget.tr("Sucessfully imported {} calibration resistor values.".format(count)))
            except Exception as exc:
                widget.parent().showException(exc)

    @QtCore.pyqtSlot()
    def onShowLogWindow(self):
        self.logWindow.toBottom()
        self.logWindow.show()
        self.logWindow.raise_()

    @QtCore.pyqtSlot()
    def onClose(self):
        self.logWindow.hide()
        self.logWindow.removeLogger(logging.getLogger())
        widget = self.view.centralWidget()
        widget.sensors().storeSettings()
        widget.controlsWidget().storeSettings()
