import datetime
import logging
import os
import re
import time
import traceback
import webbrowser

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from comet import Resource, ResourceMixin
from comet import ProcessMixin

from . import __version__
from .processes import EnvironProcess
from .processes import MeasureProcess

from .view.mainwindow import MainWindow
from .view.mainwindow import ProcessDialog
from .view.preferencesdialog import PreferencesDialog
from .view.logwindow import LogWindow

__all__ = ["Controller"]

logger = logging.getLogger(__name__)


class Controller(QtCore.QObject, ResourceMixin, ProcessMixin):
    """Main window controller."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.view = MainWindow()
        self.view.setProperty(
            "contentsUrl", "https://github.com/hephy-dd/comet-longterm"
        )
        self.view.setProperty(
            "aboutText",
            f"""<h3>Longterm It</h3>
            <p>Version {__version__}</p>
            <p>Long term sensor It measurements in CTS climate chamber.</p>
            <p>&copy; 2019-2021 hephy.at</p>""",
        )

        self.createLogWindow()
        self.createDevices()
        self.createProcesses()

        widget = self.view.centralWidget()
        widget.controlsWidget.ctsCheckBox.toggled.connect(self.onEnableEnviron)
        widget.controlsWidget.shuntBoxCheckBox.toggled.connect(self.onEnableShuntBox)
        widget.controlsWidget.started.connect(self.onStart)
        widget.controlsWidget.stopRequest.connect(self.onStopRequest)
        widget.controlsWidget.halted.connect(self.onHalted)

        # Add new menu entries
        self.view.importCalibAction.triggered.connect(self.onImportCalib)
        self.view.preferencesAction.triggered.connect(self.onShowPreferences)
        self.view.loggingAction.triggered.connect(self.onShowLogWindow)
        self.view.startAction.triggered.connect(self.view.centralWidget().controlsWidget.startPushButton.click)
        self.view.stopAction.triggered.connect(self.view.centralWidget().controlsWidget.stopPushButton.click)
        self.view.contentsAction.triggered.connect(self.onShowContents)
        self.view.aboutQtAction.triggered.connect(self.onShowAboutQt)
        self.view.aboutAction.triggered.connect(self.onShowAbout)

        self.view.closeEvent = self.closeEvent
        self.view.resize(1200, 800)
        self.view.show()

    def loadResources(self):
        settings = QtCore.QSettings()
        resources = settings.value("resources", {}, dict)
        tr = {"timeout": int}
        for name, resource in self.resources.items():
            for key, value in resources.get(name, {}).items():
                # convert types
                value = tr.get(key, str)(value)
                if key == "resource_name":
                    resource.resource_name = value
                elif key == "visa_library":
                    resource.visa_library = value
                else:
                    resource.options[key] = value

    def loadSettings(self):
        self.loadResources()
        self.view.loadSettings()
        widget = self.view.centralWidget()
        widget.sensors().loadSettings()
        widget.controlsWidget.loadSettings()

    def storeSettings(self):
        self.view.storeSettings()
        widget = self.view.centralWidget()
        widget.sensors().storeSettings()
        widget.controlsWidget.storeSettings()

    def createLogWindow(self):
        self.logWindow = LogWindow()
        self.logWindow.addLogger(logging.getLogger())
        self.logWindow.resize(640, 420)
        self.logWindow.hide()

    def createDevices(self):
        self.resources.add("shunt", Resource(resource_name="TCPIP::localhost::10001::SOCKET"))
        self.resources.add("smu", Resource(resource_name="TCPIP::localhost::10002::SOCKET"))
        self.resources.add("multi", Resource(resource_name="TCPIP::localhost::10003::SOCKET"))
        self.resources.add("cts", Resource(resource_name="TCPIP::localhost::1080::SOCKET"))

    def createProcesses(self):
        widget = self.view.centralWidget()
        # Environ process
        environ = EnvironProcess()
        environ.reading = self.onEnvironReading
        environ.failed = self.onEnvironError
        self.processes.add("environ", environ)
        self.onEnableEnviron(widget.controlsWidget.isEnvironEnabled())
        self.onEnableShuntBox(widget.controlsWidget.isShuntBoxEnabled())

        # Measurement process
        meas = MeasureProcess()

        meas.ivStarted = widget.onIvStarted
        meas.itStarted = widget.onItStarted
        meas.ivReading = widget.onMeasIvReading
        meas.itReading = widget.onMeasItReading
        meas.smuReading = widget.onSmuReading
        meas.finished = widget.onHalted

        widget.controlsWidget.stopRequest.connect(meas.stop)
        widget.controlsWidget.useShuntBoxChanged.connect(meas.setUseShuntBox)
        widget.controlsWidget.ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        widget.controlsWidget.ivStepChanged.connect(meas.setIvStep)
        widget.controlsWidget.ivDelayChanged.connect(meas.setIvDelay)
        widget.controlsWidget.biasVoltageChanged.connect(meas.setBiasVoltage)
        widget.controlsWidget.totalComplianceChanged.connect(meas.setTotalCompliance)
        widget.controlsWidget.singleComplianceChanged.connect(meas.setSingleCompliance)
        widget.controlsWidget.continueInComplianceChanged.connect(meas.setContinueInCompliance)
        widget.controlsWidget.itDurationChanged.connect(meas.setItDuration)
        widget.controlsWidget.itIntervalChanged.connect(meas.setItInterval)

        # SMU

        widget.controlsWidget.smuWidget.filterEnableChanged.connect(
            lambda enable: meas.params.update({"smu.filter.enabled": enable})
        )
        widget.controlsWidget.smuWidget.filterTypeChanged.connect(
            lambda type: meas.params.update({"smu.filter.type": type})
        )
        widget.controlsWidget.smuWidget.filterCountChanged.connect(
            lambda count: meas.params.update({"smu.filter.count": count})
        )

        # DMM

        widget.controlsWidget.dmmWidget.filterEnableChanged.connect(
            lambda enable: meas.params.update({"dmm.filter.enabled": enable})
        )
        widget.controlsWidget.dmmWidget.filterTypeChanged.connect(
            lambda type: meas.params.update({"dmm.filter.type": type})
        )
        widget.controlsWidget.dmmWidget.filterCountChanged.connect(
            lambda count: meas.params.update({"dmm.filter.count": count})
        )

        self.connectProcess(meas)
        self.processes.add("meas", meas)

    def setLevel(self, level):
        self.logWindow.setLevel(level)

    def connectProcess(self, process):
        """Connect process signals to main window slots."""
        process.failed = self.onShowException
        process.messageChanged = self.view.showMessage
        process.messageCleared = self.view.clearMessage
        process.progressChanged = self.view.showProgress
        process.progressHidden = self.view.hideProgress

    @QtCore.pyqtSlot(bool)
    def onEnableEnviron(self, enabled):
        """Enable environment process."""
        widget = self.view.centralWidget()
        # Toggle environ tab
        index = widget.bottomTabWidget.indexOf(widget.ctsTab)
        widget.bottomTabWidget.setTabEnabled(index, enabled)
        widget.statusWidget.setCtsEnabled(enabled)
        widget.statusWidget.setTemperature(float("nan"))
        widget.statusWidget.setHumidity(float("nan"))
        widget.statusWidget.setStatus("N/A")
        widget.sensorsWidget.dataChanged()  # HACK keep updated
        # Toggle environ process
        environ = self.processes.get("environ")
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
        widget.statusWidget.setTemperature(reading.get("temp"))
        widget.statusWidget.setHumidity(reading.get("humid"))
        widget.statusWidget.setStatus(
            "{} ({})".format(reading.get("status"), reading.get("program"))
        )
        meas = self.processes.get("meas")
        meas.setTemperature(reading.get("temp"))
        meas.setHumidity(reading.get("humid"))
        meas.setStatus(reading.get("status"))
        meas.setProgram(reading.get("program"))
        widget.sensorsWidget.dataChanged()  # HACK keep updated

    @QtCore.pyqtSlot(object)
    def onEnvironError(self, exc, tb=None):
        environ = self.processes.get("environ")
        # Show error only once!
        if environ.failedConnectionAttempts <= 1:
            self.onShowException(exc)

    @QtCore.pyqtSlot()
    def onStart(self):
        widget = self.view.centralWidget()
        widget.sensors().setEditable(False)
        widget.statusWidget.setCurrent(None)

        self.view.importCalibAction.setEnabled(False)
        self.view.preferencesAction.setEnabled(False)
        self.view.startAction.setEnabled(False)
        self.view.stopAction.setEnabled(True)

        # TODO
        widget.ctsChart.reset()
        widget.ivChart.load(widget.sensors())
        widget.itChart.load(widget.sensors())
        widget.ivTempChart.load(widget.sensors())
        widget.itTempChart.load(widget.sensors())
        widget.ivSourceChart.reset()
        widget.itSourceChart.reset()

        # Setup output location
        path = os.path.normpath(widget.controlsWidget.path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime(
            "%Y-%m-%dT%H-%M-%S"
        )
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.processes.get("meas")
        meas.setSensors(widget.sensors())
        meas.setUseShuntBox(widget.controlsWidget.isShuntBoxEnabled())
        meas.setIvEndVoltage(widget.controlsWidget.ivEndVoltage())
        meas.setIvStep(widget.controlsWidget.ivStep())
        meas.setIvDelay(widget.controlsWidget.ivDelay())
        meas.setBiasVoltage(widget.controlsWidget.biasVoltage())
        meas.setTotalCompliance(widget.controlsWidget.totalCompliance())
        meas.setSingleCompliance(widget.controlsWidget.singleCompliance())
        meas.setContinueInCompliance(widget.controlsWidget.continueInCompliance())
        meas.setItDuration(widget.controlsWidget.itDuration())
        meas.setItInterval(widget.controlsWidget.itInterval())
        meas.params.update({
            "smu.filter.enable": widget.controlsWidget.smuWidget.filterEnable(),
            "smu.filter.type": widget.controlsWidget.smuWidget.filterType(),
            "smu.filter.count": widget.controlsWidget.smuWidget.filterCount(),
        })
        meas.params.update({
            "dmm.filter.enable": widget.controlsWidget.dmmWidget.filterEnable(),
            "dmm.filter.type": widget.controlsWidget.dmmWidget.filterType(),
            "dmm.filter.count": widget.controlsWidget.dmmWidget.filterCount(),
        })
        meas.setPath(path)
        meas.setOperator(widget.controlsWidget.operator())

        meas.start()

    @QtCore.pyqtSlot()
    def onStopRequest(self):
        self.view.importCalibAction.setEnabled(False)
        self.view.preferencesAction.setEnabled(False)
        self.view.startAction.setEnabled(False)
        self.view.stopAction.setEnabled(False)

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.view.importCalibAction.setEnabled(True)
        self.view.preferencesAction.setEnabled(True)
        self.view.startAction.setEnabled(True)
        self.view.stopAction.setEnabled(False)

    @QtCore.pyqtSlot()
    def onImportCalib(self):
        widget = self.view.centralWidget()
        filename, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            widget,
            widget.tr("Open calibration resistors file..."),
            os.path.expanduser("~"),
        )
        if filename:
            # Yuck, quick'n dirty file parsing...
            try:
                resistors = []
                count = len(widget.sensors())
                with open(filename) as f:
                    for token in re.findall(r"\d+\s+", f.read()):
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError(
                        "Missing calibration values, expected at least {}".format(count)
                    )
                for i in range(count):
                    logger.info("sensor[%s].resistivity = %s", i, resistors[i])
                    widget.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(
                    widget,
                    widget.tr("Success"),
                    widget.tr(
                        "Sucessfully imported {} calibration resistor values.".format(
                            count
                        )
                    ),
                )
            except Exception as exc:
                self.onShowException(exc)

    def onShowPreferences(self):
        """Show modal preferences dialog."""
        dialog = PreferencesDialog(self.view)
        dialog.exec()

    def onShowLogWindow(self):
        self.logWindow.toBottom()
        self.logWindow.show()
        self.logWindow.raise_()

    def onShowContents(self):
        """Open local webbrowser with contets URL."""
        webbrowser.open(self.view.property("contentsUrl"))

    def onShowAboutQt(self):
        """Show modal about Qt dialog."""
        QtWidgets.QMessageBox.aboutQt(self.view)

    def onShowAbout(self):
        """Show modal about dialog."""
        QtWidgets.QMessageBox.about(self.view, "About", self.view.property("aboutText"))

    def onShowException(self, exc, tb=None):
        """Raise message box showing exception inforamtion."""
        logger.exception(exc)
        self.view.showMessage(self.tr("Exception occured."))
        self.view.hideProgress()
        details = "".join(traceback.format_tb(exc.__traceback__))
        dialog = QtWidgets.QMessageBox(self.view)
        dialog.setIcon(dialog.Icon.Critical)
        dialog.setWindowTitle(self.tr("Exception occured"))
        dialog.setText(format(exc))
        dialog.setDetailedText(details)
        dialog.exec()

    def closeEvent(self, event):
        dialog = QtWidgets.QMessageBox(self.view)
        dialog.setIcon(QtWidgets.QMessageBox.Question)
        dialog.setText(self.tr("Quit application?"))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setDefaultButton(QtWidgets.QMessageBox.No)
        dialog.exec()

        if dialog.result() == dialog.Yes:
            if len(self.processes):
                dialog = ProcessDialog(self.processes, self.view)
                dialog.exec()
            self.logWindow.hide()
            self.logWindow.removeLogger(logging.getLogger())
            event.accept()
        else:
            event.ignore()
