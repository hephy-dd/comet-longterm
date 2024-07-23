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

        dashboard = self.view.dashboard
        dashboard.controlsWidget.ctsCheckBox.toggled.connect(self.onEnableEnviron)
        dashboard.controlsWidget.shuntBoxCheckBox.toggled.connect(self.onEnableShuntBox)
        dashboard.controlsWidget.started.connect(self.onStart)
        dashboard.controlsWidget.stopRequest.connect(self.onStopRequest)
        dashboard.controlsWidget.halted.connect(self.onHalted)

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

    def readSettings(self):
        self.loadResources()
        self.view.readSettings()
        dashboard = self.view.dashboard
        dashboard.sensors().readSettings()
        dashboard.controlsWidget.readSettings()

    def writeSettings(self):
        self.view.writeSettings()
        dashboard = self.view.dashboard
        dashboard.sensors().writeSettings()
        dashboard.controlsWidget.writeSettings()

    def createProcesses(self):
        dashboard = self.view.dashboard
        # Environ process
        self.view.environ_worker = EnvironWorker(self.view.resources)
        self.view.environ_worker.reading.connect(self.onEnvironReading)
        self.view.environ_worker.failed.connect(self.view.onShowException)
        self.onEnableEnviron(dashboard.controlsWidget.isEnvironEnabled())
        self.onEnableShuntBox(dashboard.controlsWidget.isShuntBoxEnabled())
        self.view.environ_thread = threading.Thread(target=self.view.environ_worker)
        self.view.environ_thread.start()

        # Measurement process
        meas = MeasureWorker(self.view.resources)

        meas.ivStarted.connect(dashboard.onIvStarted)
        meas.itStarted.connect(dashboard.onItStarted)
        meas.ivReading.connect(dashboard.onMeasIvReading)
        meas.itReading.connect(dashboard.onMeasItReading)
        meas.smuReading.connect(dashboard.onSmuReading)
        meas.finished.connect(dashboard.onHalted)
        meas.failed.connect(self.view.onShowException)

        dashboard.controlsWidget.stopRequest.connect(meas.abort)
        dashboard.controlsWidget.useShuntBoxChanged.connect(meas.setUseShuntBox)
        dashboard.controlsWidget.ivEndVoltageChanged.connect(meas.setIvEndVoltage)
        dashboard.controlsWidget.ivStepChanged.connect(meas.setIvStep)
        dashboard.controlsWidget.ivDelayChanged.connect(meas.setIvDelay)
        dashboard.controlsWidget.biasVoltageChanged.connect(meas.setBiasVoltage)
        dashboard.controlsWidget.totalComplianceChanged.connect(meas.setTotalCompliance)
        dashboard.controlsWidget.singleComplianceChanged.connect(meas.setSingleCompliance)
        dashboard.controlsWidget.continueInComplianceChanged.connect(meas.setContinueInCompliance)
        dashboard.controlsWidget.itDurationChanged.connect(meas.setItDuration)
        dashboard.controlsWidget.itIntervalChanged.connect(meas.setItInterval)

        # SMU

        dashboard.controlsWidget.smuWidget.filterEnableChanged.connect(
            lambda enable: meas.params.update({"smu.filter.enabled": enable})
        )
        dashboard.controlsWidget.smuWidget.filterTypeChanged.connect(
            lambda type: meas.params.update({"smu.filter.type": type})
        )
        dashboard.controlsWidget.smuWidget.filterCountChanged.connect(
            lambda count: meas.params.update({"smu.filter.count": count})
        )

        # DMM

        dashboard.controlsWidget.dmmWidget.filterEnableChanged.connect(
            lambda enable: meas.params.update({"dmm.filter.enabled": enable})
        )
        dashboard.controlsWidget.dmmWidget.filterTypeChanged.connect(
            lambda type: meas.params.update({"dmm.filter.type": type})
        )
        dashboard.controlsWidget.dmmWidget.filterCountChanged.connect(
            lambda count: meas.params.update({"dmm.filter.count": count})
        )
        dashboard.controlsWidget.dmmWidget.channelsSlotChanged.connect(
            lambda slot: meas.params.update({"dmm.channels.slot": slot})
        )
        dashboard.controlsWidget.dmmWidget.channelsOffsetChanged.connect(
            lambda offset: meas.params.update({"dmm.channels.offset": offset})
        )
        dashboard.controlsWidget.dmmWidget.triggerDelayAutoChanged.connect(
            lambda enabled: meas.params.update({"dmm.trigger.delay_auto": enabled})
        )
        dashboard.controlsWidget.dmmWidget.triggerDelayChanged.connect(
            lambda delay: meas.params.update({"dmm.trigger.delay": delay})
        )

        self.view.meas_worker = meas
        self.view.meas_thread = threading.Thread(target=self.view.meas_worker)

    def onEnableEnviron(self, enabled):
        """Enable environment process."""
        dashboard = self.view.dashboard
        # Toggle environ tab
        index = dashboard.bottomTabWidget.indexOf(dashboard.ctsTab)
        dashboard.bottomTabWidget.setTabEnabled(index, enabled)
        dashboard.statusWidget.setCtsEnabled(enabled)
        dashboard.statusWidget.setTemperature(float("nan"))
        dashboard.statusWidget.setHumidity(float("nan"))
        dashboard.statusWidget.setStatus("N/A")
        dashboard.sensorsWidget.dataChanged()  # HACK keep updated
        # Toggle environ worker
        self.view.environ_worker.setEnabled(enabled)

    def onEnableShuntBox(self, enabled):
        """Enable shunt box."""
        # Toggle pt100 tab

    def onEnvironReading(self, reading):
        dashboard = self.view.dashboard
        dashboard.ctsChart.append(reading)
        dashboard.statusWidget.setTemperature(reading.get("temp"))
        dashboard.statusWidget.setHumidity(reading.get("humid"))
        dashboard.statusWidget.setStatus(
            "{} ({})".format(reading.get("status"), reading.get("program"))
        )
        meas = self.view.meas_worker
        meas.setTemperature(reading.get("temp"))
        meas.setHumidity(reading.get("humid"))
        meas.setStatus(reading.get("status"))
        meas.setProgram(reading.get("program"))
        dashboard.sensorsWidget.dataChanged()  # HACK keep updated

    def onStart(self):
        dashboard = self.view.dashboard
        dashboard.sensors().setEditable(False)
        dashboard.statusWidget.clearCurrent()

        self.view.importCalibAction.setEnabled(False)
        self.view.preferencesAction.setEnabled(False)
        self.view.startAction.setEnabled(False)
        self.view.stopAction.setEnabled(True)

        # TODO
        dashboard.ctsChart.reset()
        dashboard.ivChart.load(dashboard.sensors())
        dashboard.itChart.load(dashboard.sensors())
        dashboard.ivTempChart.load(dashboard.sensors())
        dashboard.itTempChart.load(dashboard.sensors())
        dashboard.ivSourceChart.reset()
        dashboard.itSourceChart.reset()

        # Setup output location
        path = os.path.normpath(dashboard.controlsWidget.path())
        timestamp = datetime.datetime.utcfromtimestamp(time.time()).strftime(
            "%Y-%m-%dT%H-%M-%S"
        )
        path = os.path.join(path, timestamp)
        if not os.path.exists(path):
            os.makedirs(path)

        meas = self.view.meas_worker
        meas.setSensors(dashboard.sensors())
        meas.setUseShuntBox(dashboard.controlsWidget.isShuntBoxEnabled())
        meas.setIvEndVoltage(dashboard.controlsWidget.ivEndVoltage())
        meas.setIvStep(dashboard.controlsWidget.ivStep())
        meas.setIvDelay(dashboard.controlsWidget.ivDelay())
        meas.setBiasVoltage(dashboard.controlsWidget.biasVoltage())
        meas.setTotalCompliance(dashboard.controlsWidget.totalCompliance())
        meas.setSingleCompliance(dashboard.controlsWidget.singleCompliance())
        meas.setContinueInCompliance(dashboard.controlsWidget.continueInCompliance())
        meas.setItDuration(dashboard.controlsWidget.itDuration())
        meas.setItInterval(dashboard.controlsWidget.itInterval())
        meas.params.update({
            "smu.filter.enable": dashboard.controlsWidget.smuWidget.filterEnable(),
            "smu.filter.type": dashboard.controlsWidget.smuWidget.filterType(),
            "smu.filter.count": dashboard.controlsWidget.smuWidget.filterCount(),
        })
        meas.params.update({
            "dmm.filter.enable": dashboard.controlsWidget.dmmWidget.filterEnable(),
            "dmm.filter.type": dashboard.controlsWidget.dmmWidget.filterType(),
            "dmm.filter.count": dashboard.controlsWidget.dmmWidget.filterCount(),
            "dmm.channels.slot": dashboard.controlsWidget.dmmWidget.channelsSlot(),
            "dmm.channels.offset": dashboard.controlsWidget.dmmWidget.channelsOffset(),
            "dmm.trigger.delay_auto": dashboard.controlsWidget.dmmWidget.triggerDelayAuto(),
            "dmm.trigger.delay": dashboard.controlsWidget.dmmWidget.triggerDelay(),
        })
        meas.setPath(path)
        meas.setOperator(dashboard.controlsWidget.operator())

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
