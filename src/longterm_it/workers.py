import csv
import contextlib
import logging
import math
import os
import re
import threading
import time
import traceback
from typing import Any, Callable, Optional

import pyvisa.errors

from PyQt5 import QtCore

from comet.functions import LinearRange

from comet.driver.cts.itc import ITC
from comet.driver.keithley import K2410
from comet.driver.keithley import K2400 as K2700  # TODO

from .driver import ShuntBox  # TODO
from .utils import make_iso
from .writers import IVWriter, ItWriter

__all__ = ["EnvironWorker", "MeasureWorker"]

logger = logging.getLogger(__name__)

driver_registry: dict[str, Callable] = {
    "smu": K2410,
    "dmm": K2700,
    "itc": ITC,
    "shuntbox": ShuntBox,
}


def get_driver(name: str) -> Callable:
    if name in driver_registry:
        return driver_registry[name]
    raise ValueError(f"no such driver: {name!r}")


def parse_reading(s):  # TODO
    """Returns list of dictionaries containing reading values."""
    readings = []
    # split '-4.32962079e-05VDC,+0.000SECS,+0.0000RDNG#,...'
    for values in re.findall(r'([^#]+)#\,?', s):
        values = re.findall(r'([+-]?\d+(?:\.\d+)?(?:E[+-]\d+)?)([A-Z]+)\,?', values)
        readings.append({suffix: float(value) for value, suffix in values})
    return readings


class AbortRequested(Exception): ...


class EnvironWorker(QtCore.QObject):
    """Environment monitoring worker. Polls for temperature, humidity and
    climate chamber running state in intervals.
    """

    interval: float = 5.0

    timeout: float = 5.0

    failedConnectionAttempts: int = 0

    failed = QtCore.pyqtSignal(Exception)
    reading = QtCore.pyqtSignal(dict)

    def __init__(self, resources, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.resources = resources
        self.abort_requested = threading.Event()
        self.isEnabled: bool = False

    def abort(self) -> None:
        self.abort_requested.set()

    def setEnabled(self, enabled: bool) -> None:
        self.isEnabled = enabled

    def read(self, device) -> dict:
        """Read environment data from device."""
        temp = device.analog_channel[1][0]
        humid = device.analog_channel[2][0]
        running = device.status.running
        # Read pause flag
        o = list(device.query_bytes("O", 14))
        if o[3] == "1":
            status = "PAUSE"
        else:
            if running:
                status = "ON"
            else:
                status = "OFF"
        program = device.program
        return {
            "time": time.time(),
            "temp": temp,
            "humid": humid,
            "status": status,
            "program": program,
        }

    def __call__(self) -> None:
        while not self.abort_requested.is_set():
            try:
                if self.isEnabled:
                    # Open connection to instrument
                    with self.resources.get("cts") as res:
                        cts = get_driver("itc")(res)
                        while not self.abort_requested.is_set() and self.isEnabled:
                            reading = self.read(cts)
                            logger.info("CTS reading: %s", reading)
                            self.reading.emit(reading)
                            self.failedConnectionAttempts = 0
                            time.sleep(self.interval)
            except Exception as exc:
                logger.exception(exc)
                if not self.failedConnectionAttempts:
                    self.failed.emit(exc)
                self.failedConnectionAttempts += 1
                time.sleep(self.timeout)
            else:
                time.sleep(1)


class MeasureWorker(QtCore.QObject):
    """Long term measurement worker, consisting of five stages:

    - ramp down, reset and setup instruments
    - ramp up to end voltage
    - ramp down to bias voltage
    - long term It measurement
    - ramp down to zero voltage

    If any of the first four stages fails, a ramp down will be executed.
    """

    failed = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()

    messageChanged = QtCore.pyqtSignal(str)
    messageCleared = QtCore.pyqtSignal()
    progressChanged = QtCore.pyqtSignal(int, int)
    progressHidden = QtCore.pyqtSignal()

    ivStarted = QtCore.pyqtSignal()
    itStarted = QtCore.pyqtSignal()
    ivReading = QtCore.pyqtSignal(object)
    itReading = QtCore.pyqtSignal(object)
    smuReading = QtCore.pyqtSignal(object)

    def __init__(self, resources, parent: Optional[QtCore.QObject] = None) -> None:
        super().__init__(parent)
        self.abort_requested = threading.Event()
        self.resources = resources
        self.params: dict[str, Any] = {}

        self.setUseShuntBox(True)
        self.setCurrentVoltage(0.0)
        self.setTemperature(float("nan"))
        self.setHumidity(float("nan"))
        self.setStatus("N/A")
        self.setProgram(0)

        self.params.update({
            "smu.route.terminals": "rear",
            "smu.filter.enable": False,
            "smu.fitler.type": "repeat",
            "smu.filter.count": 0,
        })

        self.params.update({
            "dmm.filter.enable": False,
            "dmm.fitler.type": "repeat",
            "dmm.filter.count": 0,
            "dmm.channels.slot": 1,
            "dmm.channels.offset": 0,
            "dmm.trigger.delay_auto": True,
            "dmm.trigger.delay": 0,
        })

    def abort(self) -> None:
        self.abort_requested.set()

    def sensors(self):
        return self.__sensors

    def setSensors(self, sensors):
        self.__sensors = sensors

    def startTime(self):
        return self.__startTime

    def setStartTime(self, value):
        self.__startTime = value

    def currentVoltage(self):
        return self.__currentVoltage

    def setCurrentVoltage(self, value):
        self.__currentVoltage = value

    def useShuntBox(self):
        return self.__useShuntBox

    def setUseShuntBox(self, value):
        self.__useShuntBox = value

    def ivEndVoltage(self):
        return self.__ivEndVoltage

    def setIvEndVoltage(self, value):
        self.__ivEndVoltage = value

    def ivStep(self):
        return self.__ivStep

    def setIvStep(self, value):
        self.__ivStep = value

    def ivDelay(self):
        return self.__ivDelay

    def setIvDelay(self, value):
        self.__ivDelay = value

    def biasVoltage(self):
        return self.__biasVoltage

    def setBiasVoltage(self, value):
        self.__biasVoltage = value

    def totalCompliance(self):
        return self.__totalCompliance

    def setTotalCompliance(self, value):
        self.__totalCompliance = value

    def singleCompliance(self):
        """Limited to total compliance."""
        return min(self.__singleCompliance, self.totalCompliance())

    def setSingleCompliance(self, value):
        self.__singleCompliance = value

    def continueInCompliance(self):
        return self.__continue

    def setContinueInCompliance(self, value):
        self.__continue = value

    def itDuration(self):
        return self.__itDuration

    def setItDuration(self, value):
        self.__itDuration = value

    def itInterval(self):
        return self.__itInterval

    def setItInterval(self, value):
        self.__itInterval = value

    def temperature(self):
        return self.__temperature

    def setTemperature(self, value):
        self.__temperature = value

    def humidity(self):
        return self.__humidity

    def setHumidity(self, value):
        self.__humidity = value

    def status(self):
        return self.__status

    def setStatus(self, value):
        self.__status = value

    def program(self):
        return self.__program

    def setProgram(self, value):
        self.__program = value

    def path(self):
        return self.__path

    def setPath(self, value):
        self.__path = value

    def operator(self):
        return self.__operator

    def setOperator(self, value):
        self.__operator = value

    def showMessage(self, message):
        self.messageChanged.emit(message)

    def clearMessage(self):
        self.messageCleared.emit()

    def showProgress(self, value, maximum):
        self.progressChanged.emit(value, maximum)

    def hideProgress(self):
        self.progressHidden.emit()

    def reset(self, smu, multi) -> None:
        # Reset SMU
        logger.info("Reset SMU...")
        smu.resource.write("*RST")
        smu.resource.query("*OPC?")
        time.sleep(0.500)
        smu.resource.write("*CLS")
        smu.resource.query("*OPC?")
        smu.resource.write(":SYST:BEEP:STAT OFF")
        smu.resource.query("*OPC?")
        error = smu.next_error()
        if error:
            raise RuntimeError(f"{smu.resource.resource_name}: {error.code}, {error.message}")
        # Reset multimeter
        logger.info("Reset Multimeter...")
        multi.resource.write("*RST")
        multi.resource.query("*OPC?")
        time.sleep(0.500)
        multi.resource.write("*CLS")
        multi.resource.query("*OPC?")
        multi.resource.write(":SYST:BEEP:STAT OFF")
        multi.resource.query("*OPC?")
        error = multi.next_error()
        if error:
            raise RuntimeError(f"{multi.resource.resource_name}: {error.code}, {error.message}")

    def scan(self, smu, multi) -> dict:
        """Scan selected channels and return dictionary of readings.

        time:  timestamp
        I:  total SMU current
        U:  current SMU voltage
        channels:  list of channel readings
            index:  index of channel
            I:  current
            U:  voltage
            R:  calibrated resistor value
            temp:  temperature (PT100) incl. offset
        """
        # Check SMU compliance tripped?
        compliance_tripped = int(smu.resource.query(":SENS:CURR:PROT:TRIP?"))
        if compliance_tripped:
            logger.warning("SMU in compliance!")
            if not self.continueInCompliance():
                raise ValueError(f"SMU in compliance")

        # Update SMU complicance
        total_compliance = self.totalCompliance()
        logger.info("SMU total compliance: %G A", total_compliance)
        smu.resource.write(f"SENS:CURR:PROT:LEV {total_compliance:E}")
        smu.resource.query("*OPC?")

        # SMU current
        logger.info("Read SMU current...")
        totalCurrent = float(smu.resource.query(":READ?").split(",")[1])
        logger.info(f"SMU current: {totalCurrent:G} A")

        # Read temperatures and shunt box stats
        temperature: dict = {}
        shuntbox: dict = {"uptime": 0, "memory": 0}
        if self.useShuntBox():
            with self.resources.get("shunt") as res:
                shunt = get_driver("shuntbox")(res)
                shuntbox["uptime"] = shunt.uptime()
                shuntbox["memory"] = shunt.memory()
                for index, value in enumerate(shunt.temperature()):
                    temperature[index + 1] = value

        # start measurement
        logger.info("Initiate measurement...")
        multi.resource.write("*CLS")
        multi.resource.write("*OPC")
        multi.resource.write(":INIT")
        done = False
        retries = 40
        for i in range(retries):
            if 1 == int(multi.resource.query("*ESR?")) & 0x1:
                done = True
                break
            time.sleep(0.250)
        if not done:
            raise RuntimeError("failed to poll for ESR")
        logger.info("Read results buffer...")
        results = parse_reading(multi.resource.query(":FETC?"))

        for index, result in enumerate(results):
            logger.info("[%d]: %s", index, result)

        channels = {}
        for sensor in self.sensors():
            if sensor.enabled:
                R = sensor.resistivity  # ohm, from calibration measurement array
                U = results.pop(0).get("VDC", 0)  # pop result
                # Calculate sensor current
                I = U / R
                if abs(I) > self.singleCompliance():
                    sensor.status = sensor.State.COMPL_ERR
                    # Switch HV relay off
                    if self.useShuntBox():
                        with self.resources.get("shunt") as res:
                            shunt = get_driver("shuntbox")(res)
                            shunt.set_relay(sensor.index, False)
                            sensor.hv = False
                temp = temperature.get(sensor.index, float("nan"))
                channels[sensor.index] = {
                    "index": sensor.index,
                    "I": I,
                    "U": U,
                    "R": R,
                    "temp": temp + sensor.temperature_offset,
                }

        if len(results):
            raise RuntimeError("Too many results in buffer.")

        return {
            "time": time.time(),
            "channels": channels,
            "I": totalCurrent,
            "U": self.currentVoltage(),
            "shuntbox": shuntbox,
        }

    def setup(self, smu, multi) -> None:
        """Setup SMU and Multimeter instruments."""

        self.showMessage("Clear buffers")
        self.setStartTime(time.time())

        for sensor in self.sensors():
            sensor.status = sensor.State.OK

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)

        # Optional ramp down SMU
        value = float(smu.resource.query(":SOUR:VOLT:LEV?"))
        self.setCurrentVoltage(value)
        self.rampDown(smu, multi)

        # Reset instruments
        self.reset(smu, multi)

        # Read instrument identifications
        idn = multi.resource.query("*IDN?").strip()
        logger.info("Multimeter: %s", idn)

        idn = smu.resource.query("*IDN?").strip()
        logger.info("Source Unit: %s", idn)

        if self.useShuntBox():
            with self.resources.get("shunt") as res:
                shunt = get_driver("shuntbox")(res)
                idn = shunt.identify()
                logger.info("HEPHY ShuntBox: %s", idn)

        self.showMessage("Setup multimeter")
        self.showProgress(1, 3)

        n_channels = len(self.sensors())

        dmm_channels_slot = self.params.get("dmm.channels.slot", 1)
        logger.info("dmm.channels.slot: %s", dmm_channels_slot)

        dmm_channels_offset = self.params.get("dmm.channels.offset", 0)
        logger.info("dmm.channels.offset: %s", dmm_channels_offset)

        offset = (dmm_channels_slot * 100) + dmm_channels_offset

        multi.resource.write(f':FUNC "VOLT:DC", (@{offset+1}:{offset+1+n_channels})')
        multi.resource.query("*OPC?")
        # delete instrument buffer
        multi.resource.write(":TRACE:CLEAR")
        multi.resource.query("*OPC?")
        # turn off continous measurements
        multi.resource.write(":INIT:CONT OFF")
        multi.resource.query("*OPC?")
        # set trigger source immediately
        multi.resource.write(":TRIG:SOUR IMM")
        multi.resource.query("*OPC?")

        # set channels to scan (up to max 10)
        channels = []
        for sensor in self.sensors():
            if sensor.enabled:
                channels.append(format(offset + sensor.index))
        if not channels:
            raise RuntimeError("No sensor channels selected!")

        sample_count = len(channels)

        # ROUTE:SCAN (@101,102,103...)
        logger.info("channels: %s", ",".join(channels))
        multi.resource.write("ROUTE:SCAN (@{})".format(",".join(channels)))
        multi.resource.query("*OPC?")

        multi.resource.write(":TRIG:COUN 1")
        multi.resource.query("*OPC?")

        logger.info("sample count: %d", sample_count)
        multi.resource.write(f":SAMP:COUN {sample_count}")
        multi.resource.query("*OPC?")
        # start scan when triggered
        multi.resource.write(":ROUT:SCAN:TSO IMM")
        multi.resource.query("*OPC?")
        # enable scan
        multi.resource.write(":ROUT:SCAN:LSEL INT")
        multi.resource.query("*OPC?")

        # Filter
        dmm_filter_enable = self.params.get("dmm.filter.enable", False)
        logger.info("dmm.filter.enable: %s", dmm_filter_enable)
        multi.resource.write(f":SENS:VOLT:AVER:STAT {dmm_filter_enable:d}")
        multi.resource.query("*OPC?")

        if int(multi.resource.query(":SENS:VOLT:AVER:STAT?").strip()) != dmm_filter_enable:
            raise RuntimeError("failed to configure dmm.filter.enable")

        dmm_filter_type: str = self.params.get("dmm.filter.type", "repeat")
        logger.info("dmm.filter.type: %s", dmm_filter_type)
        tcontrol = {"repeat": "REP", "moving": "MOV"}[dmm_filter_type]
        multi.resource.write(f":SENS:VOLT:AVER:TCON {tcontrol}")
        multi.resource.query("*OPC?")

        if multi.resource.query(":SENS:VOLT:AVER:TCON?").strip() != tcontrol:
            raise RuntimeError("failed to configure dmm.filter.type")

        dmm_filter_count = self.params.get("dmm.filter.count", 10)
        logger.info("dmm.filter.count: %s", dmm_filter_count)
        multi.resource.write(f":SENS:VOLT:AVER:COUN {dmm_filter_count:d}")
        multi.resource.query("*OPC?")

        if int(multi.resource.query(":SENS:VOLT:AVER:COUN?").strip()) != dmm_filter_count:
            raise RuntimeError("failed to configure dmm.filter.count")

        dmm_trigger_delay_auto = self.params.get("dmm.trigger.delay_auto", False)
        logger.info("dmm.trigger.delay_auto: %s", dmm_trigger_delay_auto)
        multi.resource.write(f":TRIG:DEL:AUTO {dmm_trigger_delay_auto:d}")
        multi.resource.query("*OPC?")

        if bool(int(multi.resource.query(":TRIG:DEL:AUTO?").strip())) != dmm_trigger_delay_auto:
            raise RuntimeError("failed to configure dmm.trigger.delay_auto")

        dmm_trigger_delay = self.params.get("dmm.trigger.delay", 0)
        logger.info("dmm.trigger.delay: %s", dmm_trigger_delay)

        if not dmm_trigger_delay_auto:
            multi.resource.write(f":TRIG:DEL {dmm_trigger_delay:E}")
            multi.resource.query("*OPC?")

            if float(multi.resource.query(":TRIG:DEL?").strip()) != dmm_trigger_delay:
                raise RuntimeError("failed to configure dmm.trigger.delay")

        self.showMessage("Setup source unit")
        self.showProgress(2, 3)

        smu_route_terminal = self.params.get("smu.route.terminals", "rear")
        logger.info("smu.route.terminal: %s", smu_route_terminal)
        terminal = {"front": "FRON", "rear": "REAR"}[smu_route_terminal]
        smu.resource.write(f":ROUT:TERM {terminal}")
        smu.resource.query("*OPC?")

        smu.resource.write(":SOUR:FUNC VOLT")
        smu.resource.query("*OPC?")
        # switch output OFF
        smu.output = False
        smu.resource.write("SOUR:VOLT:RANG MAX")
        smu.resource.query("*OPC?")
        # measure current DC
        smu.resource.write('SENS:FUNC "CURR"')
        smu.resource.query("*OPC?")
        # output data format
        smu.resource.write("SENS:CURR:RANG:AUTO 1")
        smu.resource.query("*OPC?")
        smu.resource.write("TRIG:CLE")
        smu.resource.query("*OPC?")

        # Filter
        smu_filter_enable = self.params.get("smu.filter.enable", False)
        logger.info("smu.filter.enable: %s", smu_filter_enable)
        smu.resource.write(f":SENS:AVER:STAT {smu_filter_enable:d}")
        smu.resource.query("*OPC?")

        smu_filter_type = self.params.get("smu.filter.type", "repeat")
        logger.info("smu.filter.type: %s", smu_filter_type)
        tcontrol = {"repeat": "REP", "moving": "MOV"}[smu_filter_type]
        smu.resource.write(f":SENS:AVER:TCON {tcontrol}")
        smu.resource.query("*OPC?")

        smu_filter_count = self.params.get("smu.filter.count", 10)
        logger.info("smu.filter.count: %s", smu_filter_count)
        smu.resource.write(f":SENS:AVER:COUN {smu_filter_count:d}")
        smu.resource.query("*OPC?")

        # Set SMU complicance
        total_compliance = self.totalCompliance()
        smu.resource.write(f"SENS:CURR:PROT:LEV {total_compliance:E}")
        smu.resource.query("*OPC?")

        # clear voltage
        self.setCurrentVoltage(0.0)
        smu.resource.write(f":SOUR:VOLT:LEV {self.currentVoltage():E}")
        smu.resource.query("*OPC?")

        # switch output ON
        smu.resource.write(":OUTP:STAT ON")
        smu.resource.query("*OPC?")

        # Enable active shunt box channels
        if self.useShuntBox():
            with self.resources.get("shunt") as res:
                shunt = get_driver("shuntbox")(res)
                for sensor in self.sensors():
                    shunt.set_relay(sensor.index, sensor.enabled)
                    sensor.hv = sensor.enabled
        else:
            for sensor in self.sensors():
                sensor.hv = None

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self, smu, multi) -> bool:
        """Ramp up SMU voltage to end voltage."""
        self.showMessage("Ramping up")
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.ivStarted.emit()
        t0 = time.time()
        with contextlib.ExitStack() as stack:
            writers = {}
            timestamp = make_iso(self.startTime())
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    filename = os.path.join(self.path(), f"IV-{name}-{timestamp}.txt")
                    f = open(filename, "w", newline="")
                    writer = IVWriter(stack.enter_context(f))
                    writer.write_meta(sensor, self.operator(), timestamp, self.ivEndVoltage())
                    writer.write_header()
                    writers[sensor.index] = writer
            step = (
                -self.ivStep()
                if self.ivEndVoltage() < self.currentVoltage()
                else self.ivStep()
            )
            for value in LinearRange(self.currentVoltage(), self.ivEndVoltage(), step):
                if self.abort_requested.is_set():
                    raise AbortRequested()
                self.setCurrentVoltage(value)
                self.showMessage(f"Ramping up ({value:.2f} V)")
                # Set voltage
                smu.resource.write(f":SOUR:VOLT:LEV {value:E}")
                smu.resource.query("*OPC?")
                self.showProgress(self.currentVoltage(), self.ivEndVoltage())
                time.sleep(self.ivDelay())
                reading = self.scan(smu, multi)
                logger.info("scan reading: %s", reading)
                self.ivReading.emit(reading)
                self.smuReading.emit({"U": self.currentVoltage(), "I": reading.get("I")})
                for sensor in self.sensors():
                    if sensor.enabled:
                        # Time delta since start of IV
                        dt = time.time() - t0
                        writers[sensor.index].write_row(
                            timestamp=dt,
                            voltage=reading.get("U", math.nan),
                            current=reading.get("channels", {})[sensor.index].get("I", math.nan),
                            smu_current=reading.get("I", math.nan),
                            pt100=reading.get("channels", {})[sensor.index].get("temp", math.nan),
                            cts_temperature=self.temperature(),
                            cts_humidity=self.humidity(),
                            cts_status=self.status(),
                            cts_program=self.program(),
                            hv_status=sensor.hv,
                        )
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.showMessage("Done")
        return True

    def rampBias(self, smu, multi) -> None:
        """Ramp down SMU voltage to bias voltage."""
        startVoltage = self.currentVoltage() - self.biasVoltage()
        deltaVoltage = startVoltage - self.currentVoltage()
        self.showMessage("Ramping to bias")
        self.showProgress(deltaVoltage, startVoltage)
        step = (
            -self.ivStep()
            if self.biasVoltage() < self.currentVoltage()
            else self.ivStep()
        )
        for value in LinearRange(self.currentVoltage(), self.biasVoltage(), step):
            if self.abort_requested.is_set():
                raise AbortRequested()
            self.setCurrentVoltage(value)
            self.showMessage(f"Ramping to bias ({value:.2f} V)")
            # Set voltage
            smu.resource.write(f":SOUR:VOLT:LEV {value:E}")
            smu.resource.query("*OPC?")
            deltaVoltage = startVoltage - self.currentVoltage()
            self.showProgress(deltaVoltage, startVoltage)
            time.sleep(self.ivDelay())
            totalCurrent = float(smu.resource.query(":READ?").split(",")[1])
            self.smuReading.emit({"U": self.currentVoltage(), "I": totalCurrent})
        self.showMessage("Done")

    def longterm(self, smu, multi) -> None:
        """Run long term measurement."""
        self.showMessage("Measuring...")
        self.itStarted.emit()
        timeBegin = time.time()
        timeEnd = timeBegin + self.itDuration()
        if self.itDuration():
            self.showProgress(0, timeEnd - timeBegin)
        else:
            self.showProgress(0, 0)  # progress unknown, infinite run
        t0 = time.time()
        with contextlib.ExitStack() as stack:
            writers = {}
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = make_iso(self.startTime())
                    filename = os.path.join(self.path(), f"it-{name}-{timestamp}.txt")
                    f = open(filename, "w", newline="")
                    writer = ItWriter(stack.enter_context(f))
                    writer.write_meta(sensor, self.operator(), timestamp, self.ivEndVoltage())
                    writer.write_header()
                    writers[sensor.index] = writer
            while not self.abort_requested.is_set():
                self.showMessage("Measuring...")
                currentTime = time.time()
                if self.itDuration():
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                reading = self.scan(smu, multi)
                logger.info("scan reading: %s", reading)
                self.itReading.emit(reading)
                self.smuReading.emit({"U": self.currentVoltage(), "I": reading.get("I")})
                for sensor in self.sensors():
                    if sensor.enabled:
                        # Time delta since start of IV
                        dt = time.time() - t0
                        writers[sensor.index].write_row(
                            timestamp=dt,
                            voltage=reading.get("U", math.nan),
                            current=reading.get("channels", {})[sensor.index].get("I", math.nan),
                            smu_current=reading.get("I", math.nan),
                            pt100=reading.get("channels", {})[sensor.index].get("temp", math.nan),
                            cts_temperature=self.temperature(),
                            cts_humidity=self.humidity(),
                            cts_status=self.status(),
                            cts_program=self.program(),
                            hv_status=sensor.hv,
                        )
                # Wait...
                interval = self.itInterval()
                interval_step = 0.25
                while interval > 0:
                    if self.abort_requested.is_set():
                        raise AbortRequested()
                    time.sleep(interval_step)
                    self.showMessage(f"Next measurement in {interval:.0f} s")
                    interval -= interval_step
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self, smu, multi) -> None:
        """Ramp down SMU voltage to zero."""
        minimumStep = 5.0  # quick ramp down minimum step
        zeroVoltage = 0.0
        startVoltage = self.currentVoltage()
        deltaVoltage = startVoltage - self.currentVoltage()
        self.showMessage("Ramping down")
        self.showProgress(deltaVoltage, startVoltage)
        ivStep = max(minimumStep, self.ivStep())
        step = -ivStep if zeroVoltage < self.currentVoltage() else ivStep
        for value in LinearRange(self.currentVoltage(), zeroVoltage, step):
            # Ramp down at any cost to save lives!
            self.setCurrentVoltage(value)
            self.showMessage(f"Ramping to zero ({value:.2f} V)")
            # Set voltage
            smu.resource.write(f":SOUR:VOLT:LEV {value:E}")
            smu.resource.query("*OPC?")
            deltaVoltage = startVoltage - self.currentVoltage()
            self.showProgress(deltaVoltage, startVoltage)
            time.sleep(0.25)  # value from labview
            self.smuReading.emit({"U": self.currentVoltage(), "I": None})

        # Diable all shunt box channels
        if self.useShuntBox():
            with self.resources.get("shunt") as res:
                shunt = get_driver("shuntbox")(res)
                shunt.set_all_relays(False)
                for sensor in self.sensors():
                    sensor.hv = False

        # switch output OFF
        smu.resource.write(":OUTP:STAT OFF")

        self.showMessage("Done")

    def __call__(self) -> None:
        try:
            # Open connection to instruments
            with contextlib.ExitStack() as stack:
                smu = get_driver("smu")(stack.enter_context(self.resources.get("smu")))
                multi = get_driver("dmm")(stack.enter_context(self.resources.get("multi")))
                try:
                    self.setup(smu, multi)
                    self.rampUp(smu, multi)
                    self.rampBias(smu, multi)
                    self.longterm(smu, multi)
                except AbortRequested:
                    ...
                finally:
                    self.rampDown(smu, multi)
                    self.showMessage("Stopped")
                    self.hideProgress()
        except Exception as exc:
            logger.exception(exc)
            self.failed.emit(exc)
        finally:
            self.finished.emit()
            self.abort_requested = threading.Event()
