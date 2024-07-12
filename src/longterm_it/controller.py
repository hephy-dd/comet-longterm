import datetime
import logging
import os
import re
import time
import threading

from PyQt5 import QtCore, QtWidgets


from . import __version__
from .resource import Resource
from .workers import EnvironWorker, MeasureWorker

__all__ = ["Controller"]

logger = logging.getLogger(__name__)


class Controller:
    """Main window controller."""

    def __init__(self, view):
        self.view = view

        # regster resources
        self.view.resources.update({"shunt": Resource("TCPIP::localhost::10001::SOCKET")})
        self.view.resources.update({"smu": Resource("TCPIP::localhost::10002::SOCKET")})
        self.view.resources.update({"multi": Resource("TCPIP::localhost::10003::SOCKET")})
        self.view.resources.update({"cts": Resource("TCPIP::localhost::1080::SOCKET")})

        self.createProcesses()

        widget = self.view.centralWidget()
        widget.controlsWidget.ctsCheckBox.toggled.connect(self.onEnableEnviron)
        widget.controlsWidget.shuntBoxCheckBox.toggled.connect(self.onEnableShuntBox)
        widget.controlsWidget.started.connect(self.onStart)
        widget.controlsWidget.stopRequest.connect(self.onStopRequest)
        widget.controlsWidget.halted.connect(self.onHalted)

    def loadResources(self):
        settings = QtCore.QSettings()
        resources = settings.value("resources2", {}, dict)
        # Migrate old style settings (<= 0.12.x)
        if not resources:
            for name, resource_name in settings.value("resources", {}, dict).items():
                resources.update({name: {"resource_name": resource_name}})
        tr = {"timeout": int}
        for name, resource in self.view.resources.items():
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

    def createProcesses(self):
        widget = self.view.centralWidget()
        # Environ process
        self.view.environ_worker = EnvironWorker(self.view.resources)
        self.view.environ_worker.reading.connect(self.onEnvironReading)
        self.view.environ_worker.failed.connect(self.view.onShowException)
        self.onEnableEnviron(widget.controlsWidget.isEnvironEnabled())
        self.onEnableShuntBox(widget.controlsWidget.isShuntBoxEnabled())
        self.view.environ_thread = threading.Thread(target=self.view.environ_worker)
        self.view.environ_thread.start()

        # Measurement process
        meas = MeasureWorker(self.view.resources)

        meas.ivStarted.connect(widget.onIvStarted)
        meas.itStarted.connect(widget.onItStarted)
        meas.ivReading.connect(widget.onMeasIvReading)
        meas.itReading.connect(widget.onMeasItReading)
        meas.smuReading.connect(widget.onSmuReading)
        meas.finished.connect(widget.onHalted)

        widget.controlsWidget.stopRequest.connect(meas.abort)
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
        widget.controlsWidget.dmmWidget.channelsSlotChanged.connect(
            lambda slot: meas.params.update({"dmm.channels.slot": slot})
        )
        widget.controlsWidget.dmmWidget.channelsOffsetChanged.connect(
            lambda offset: meas.params.update({"dmm.channels.offset": offset})
        )
        widget.controlsWidget.dmmWidget.triggerDelayChanged.connect(
            lambda delay: meas.params.update({"dmm.trigger.delay": delay})
        )

        self.view.meas_worker = meas
        self.view.meas_thread = threading.Thread(target=self.view.meas_worker)

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
        # Toggle environ worker
        self.view.environ_worker.setEnabled(enabled)

    def onEnableShuntBox(self, enabled):
        """Enable shunt box."""
        # Toggle pt100 tab

    def onEnvironReading(self, reading):
        widget = self.view.centralWidget()
        widget.ctsChart.append(reading)
        widget.statusWidget.setTemperature(reading.get("temp"))
        widget.statusWidget.setHumidity(reading.get("humid"))
        widget.statusWidget.setStatus(
            "{} ({})".format(reading.get("status"), reading.get("program"))
        )
        meas = self.view.meas_worker
        meas.setTemperature(reading.get("temp"))
        meas.setHumidity(reading.get("humid"))
        meas.setStatus(reading.get("status"))
        meas.setProgram(reading.get("program"))
        widget.sensorsWidget.dataChanged()  # HACK keep updated

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

        meas = self.view.meas_worker
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
            "dmm.channels.slot": widget.controlsWidget.dmmWidget.channelsSlot(),
            "dmm.channels.offset": widget.controlsWidget.dmmWidget.channelsOffset(),
            "dmm.trigger.delay": widget.controlsWidget.dmmWidget.triggerDelay(),
        })
        meas.setPath(path)
        meas.setOperator(widget.controlsWidget.operator())

        self.view.meas_thread = threading.Thread(target=self.view.meas_worker)
        self.view.meas_thread.start()

    def onStopRequest(self):
        self.view.importCalibAction.setEnabled(False)
        self.view.preferencesAction.setEnabled(False)
        self.view.startAction.setEnabled(False)
        self.view.stopAction.setEnabled(False)

    def onHalted(self):
        self.view.importCalibAction.setEnabled(True)
        self.view.preferencesAction.setEnabled(True)
        self.view.startAction.setEnabled(True)
        self.view.stopAction.setEnabled(False)
