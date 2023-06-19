import logging
import csv
import contextlib
import time
import os
import traceback

import pyvisa.errors

from PyQt5 import QtCore

from comet import Process, StopRequest, Range
from comet import DeviceMixin

from .utils import make_iso
from .writers import IVWriter, ItWriter

logger = logging.getLogger(__name__)

class EnvironProcess(Process, DeviceMixin):
    """Environment monitoring process. Polls for temperature, humidity and
    climate chamber running state in intervals.
    """

    reading = QtCore.pyqtSignal(object)
    """Emitted when reading available, contains reading data."""

    interval = 5.0

    timeout = 5.0

    failedConnectionAttempts = 0 # HACK

    def read(self, device):
        """Read environment data from device."""
        temp = device.analog_channel(1)[0]
        humid = device.analog_channel(2)[0]
        running = device.status.running
        # Read pause flag
        o = list(device.query_bytes('O', 14))
        if o[3] == '1':
            status = 'PAUSE'
        else:
            if running:
                status = 'ON'
            else:
                status = 'OFF'
        program = device.program
        return dict(time=self.time(), temp=temp, humid=humid, status=status, program=program)

    def run(self):
        while not self.stopRequested():
            try:
                # Open connection to instrument
                with self.devices().get('cts') as cts:
                    while not self.stopRequested():
                        try:
                            reading = self.read(cts)
                        except pyvisa.errors.Error as e:
                            self.handleException(e)
                        else:
                            logger.info("CTS reading: %s", reading)
                            self.reading.emit(reading)
                        self.sleep(self.interval)
                        self.failedConnectionAttempts = 0
            except Exception as e:
                self.handleException(e)
                self.failedConnectionAttempts += 1
                self.sleep(self.timeout)

class MeasureProcess(Process, DeviceMixin):
    """Long term measurement process, consisting of five stages:

    - ramp down, reset and setup instruments
    - ramp up to end voltage
    - ramp down to bias voltage
    - long term It measurement
    - ramp down to zero voltage

    If any of the first four stages fails, a ramp down will be executed.
    """

    ivReading = QtCore.pyqtSignal(object)
    """Emitted when IV reading available, contains reading data."""

    itReading = QtCore.pyqtSignal(object)
    """Emitted when It reading available, contains reading data."""

    ivStarted = QtCore.pyqtSignal()
    """Emitted just before IV measurement starts."""

    itStarted = QtCore.pyqtSignal()
    """Emitted just before It measurement starts."""

    smuReading = QtCore.pyqtSignal(object)
    """Emitted when SMU reading available."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setUseShuntBox(True)
        self.setCurrentVoltage(0.0)
        self.setTemperature(float('nan'))
        self.setHumidity(float('nan'))
        self.setStatus('N/A')
        self.setProgram(0)
        self.setFilterEnable(False)
        self.setFilterType('repeat')
        self.setFilterCount(10)

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

    def biasVoltage(self,):
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

    def filterEnable(self):
        return self.__filterEnable

    def setFilterEnable(self, enabled):
        self.__filterEnable = enabled

    def filterType(self):
        return self.__filterType

    def setFilterType(self, type):
        assert type in ('repeat', 'moving')
        self.__filterType = type

    def filterCount(self):
        return self.__filterCount

    def setFilterCount(self, count):
        assert 0 <= count <= 100
        self.__filterCount = count

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

    def reset(self, smu, multi):
        # Reset SMU
        logger.info("Reset SMU...")
        smu.resource.write('*RST')
        smu.resource.query('*OPC?')
        self.sleep(.500)
        smu.resource.write('*CLS')
        smu.resource.query('*OPC?')
        smu.system.beeper.status = 0
        code, message = smu.system.error
        if code:
            raise RuntimeError(f"{smu.resource.resource_name}: {code}, {message}")
        # Reset multimeter
        logger.info("Reset Multimeter...")
        multi.resource.write('*RST')
        multi.resource.query('*OPC?')
        self.sleep(.500)
        multi.resource.write('*CLS')
        multi.resource.query('*OPC?')
        multi.system.beeper.status = 0
        code, message = multi.system.error
        if code:
            raise RuntimeError(f"{multi.resource.resource_name}: {code}, {message}")

    def scan(self, smu, multi):
        """Scan selected channels and return dictionary of readings.

        time:  timestamp
        I:  total SMU current
        U:  current SMU voltage
        channels:  list of channel readings
            index:  index of channel
            I:  current
            U:  voltage
            R:  calibrated resistor value
            temp:  temperature (PT100)
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
        smu.resource.write(f'SENS:CURR:PROT:LEV {total_compliance:E}')
        smu.resource.query('*OPC?')

        # SMU current
        logger.info("Read SMU current...")
        totalCurrent = smu.read()[1]
        logger.info(f"SMU current: {totalCurrent:G} A")

        # Read temperatures and shunt box stats
        temperature = {}
        shuntbox = dict(uptime=0, memory=0)
        if self.useShuntBox():
            with self.devices().get('shunt') as shunt:
                shuntbox['uptime'] = shunt.uptime
                shuntbox['memory'] = shunt.memory
                for index, value in enumerate(shunt.temperature):
                    temperature[index + 1] = value

        # start measurement
        logger.info("Initiate measurement...")
        multi.init()
        logger.info("Read results buffer...")
        results = multi.fetch()

        for index, result in enumerate(results):
            logger.info("[%d]: %s", index, result)

        channels = {}
        for sensor in self.sensors():
            if sensor.enabled:
                R = sensor.resistivity # ohm, from calibration measurement array
                U = results.pop(0).get('VDC', 0) # pop result
                # Calculate sensor current
                I = U / R
                if abs(I) > self.singleCompliance():
                    sensor.status = sensor.State.COMPL_ERR
                    # Switch HV relay off
                    if self.useShuntBox():
                        with self.devices().get('shunt') as shunt:
                            shunt.enable(sensor.index, False)
                            sensor.hv = False
                temp = temperature.get(sensor.index, float('nan'))
                channels[sensor.index] = dict(
                    index=sensor.index,
                    I=I, U=U, R=R,
                    temp=temp
                )

        if len(results):
            raise RuntimeError("Too many results in buffer.")

        return dict(
            time=self.time(),
            channels=channels,
            I=totalCurrent,
            U=self.currentVoltage(),
            shuntbox=shuntbox
        )

    def setup(self, smu, multi):
        """Setup SMU and Multimeter instruments."""

        self.showMessage("Clear buffers")
        self.setStartTime(self.time())

        for sensor in self.sensors():
            sensor.status = sensor.State.OK

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)

        # Optional ramp down SMU
        self.setCurrentVoltage(smu.source.voltage.level)
        self.rampDown(smu, multi)

        # Reset instruments
        self.reset(smu, multi)

        # Read instrument identifications
        idn = multi.identification()
        logger.info("Multimeter: %s", idn)
        idn = smu.identification()
        logger.info("Source Unit: %s", idn)
        if self.useShuntBox():
            with self.devices().get('shunt') as shunt:
                idn = shunt.identification
                logger.info("HEPHY ShuntBox: %s", idn)

        self.showMessage("Setup multimeter")
        self.showProgress(1, 3)
        multi.resource.write(':FUNC "VOLT:DC", (@101:110)')
        multi.resource.query('*OPC?')
        # delete instrument buffer
        multi.resource.write(':TRACE:CLEAR')
        multi.resource.query('*OPC?')
        # turn off continous measurements
        multi.resource.write(':INIT:CONT OFF')
        multi.resource.query('*OPC?')
        # set trigger source immediately
        multi.resource.write(':TRIG:SOUR IMM')
        multi.resource.query('*OPC?')

        # set channels to scan (up to max 10)
        channels = []
        offset = 100
        for sensor in self.sensors():
            if sensor.enabled:
                channels.append(format(offset + sensor.index))
        if not channels:
            raise RuntimeError("No sensor channels selected!")

        count = len(channels)

        # ROUTE:SCAN (@101,102,103...)
        logger.info("channels: %s", ','.join(channels))
        multi.resource.write('ROUTE:SCAN (@{})'.format(','.join(channels)))
        multi.resource.query('*OPC?')

        multi.resource.write(':TRIG:COUN 1')
        multi.resource.query('*OPC?')

        logger.info("sample count: %d", count)
        multi.resource.write(f':SAMP:COUN {count}')
        multi.resource.query('*OPC?')
        # start scan when triggered
        multi.resource.write(':ROUT:SCAN:TSO IMM')
        multi.resource.query('*OPC?')
        # enable scan
        multi.resource.write(':ROUT:SCAN:LSEL INT')
        multi.resource.query('*OPC?')

        # Filter
        logger.info("multimeter.filter.enable: %s", self.filterEnable())
        enable = int(self.filterEnable())
        multi.resource.write(f':SENS:VOLT:AVER:STAT {enable}')
        multi.resource.query('*OPC?')
        assert int(multi.resource.query(':SENS:VOLT:AVER:STAT?')) == enable

        logger.info("multimeter.filter.type: %s", self.filterType())
        tcontrol = {'repeat': 'REP', 'moving': 'MOV'}[self.filterType()]
        multi.resource.write(f':SENS:VOLT:AVER:TCON {tcontrol}')
        multi.resource.query('*OPC?')
        assert multi.resource.query(':SENS:VOLT:AVER:TCON?') == tcontrol

        logger.info("multimeter.filter.count: %s", self.filterCount())
        count = self.filterCount()
        multi.resource.write(f':SENS:VOLT:AVER:COUN {count}')
        multi.resource.query('*OPC?')
        assert int(multi.resource.query(':SENS:VOLT:AVER:COUN?')) == count

        self.showMessage("Setup source unit")
        self.showProgress(2, 3)
        smu.resource.write('SENS:AVER:TCON REP')
        smu.resource.query('*OPC?')
        smu.resource.write('SENS:AVER ON')
        smu.resource.query('*OPC?')
        smu.resource.write('ROUT:TERM REAR')
        smu.resource.query('*OPC?')
        smu.resource.write(':SOUR:FUNC VOLT')
        smu.resource.query('*OPC?')
        # switch output OFF
        smu.output = 'off'
        smu.resource.write('SOUR:VOLT:RANG MAX')
        smu.resource.query('*OPC?')
        # measure current DC
        smu.resource.write('SENS:FUNC "CURR"')
        smu.resource.query('*OPC?')
        # output data format
        smu.resource.write('SENS:CURR:RANG:AUTO 1')
        smu.resource.query('*OPC?')
        smu.resource.write('TRIG:CLE')
        smu.resource.query('*OPC?')
        smu.resource.write('SENS:AVER:TCON REP')
        smu.resource.query('*OPC?')
        smu.resource.write('SENS:AVER OFF')
        smu.resource.query('*OPC?')
        smu.resource.write('ROUT:TERM REAR')
        smu.resource.query('*OPC?')

        # Set SMU complicance
        total_compliance = self.totalCompliance()
        smu.resource.write(f'SENS:CURR:PROT:LEV {total_compliance:E}')
        smu.resource.query('*OPC?')

        # Force output enable line (connected with chamber door)
        smu.resource.write(':OUTP:ENAB ON')
        smu.resource.query('*OPC?')

        # clear voltage
        self.setCurrentVoltage(0.0)
        smu.source.voltage.level = self.currentVoltage()
        # switch output ON
        smu.output = 'on'

        # Enable active shunt box channels
        if self.useShuntBox():
            with self.devices().get('shunt') as shunt:
                for sensor in self.sensors():
                    shunt.enable(sensor.index, sensor.enabled)
                    sensor.hv = sensor.enabled
        else:
            for sensor in self.sensors():
                sensor.hv = None

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self, smu, multi):
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
                    filename = os.path.join(self.path(), f'IV-{name}-{timestamp}.txt')
                    f = open(filename, 'w', newline='')
                    writer = IVWriter(stack.enter_context(f))
                    writer.write_meta(sensor, self.operator(), timestamp, self.ivEndVoltage())
                    writer.write_header()
                    writers[sensor.index] = writer
            step = -self.ivStep() if self.ivEndVoltage() < self.currentVoltage() else self.ivStep()
            for value in Range(self.currentVoltage(), self.ivEndVoltage(), step):
                self.setCurrentVoltage(value)
                if not self.stopRequested():
                    self.showMessage(f"Ramping up ({value:.2f} V)")
                    # Set voltage
                    smu.source.voltage.level = value
                    self.showProgress(self.currentVoltage(), self.ivEndVoltage())
                    self.sleep(self.ivDelay())
                    reading = self.scan(smu, multi)
                    logger.info("scan reading: %s", reading)
                    self.ivReading.emit(reading)
                    self.smuReading.emit(dict(U=self.currentVoltage(), I=reading.get('I')))
                    for sensor in self.sensors():
                        if sensor.enabled:
                            # Time delta since start of IV
                            dt = time.time() - t0
                            writers[sensor.index].write_row(
                                timestamp=dt,
                                voltage=reading.get('U'),
                                current=reading.get('channels')[sensor.index].get('I'),
                                smu_current=reading.get('I'),
                                pt100=reading.get('channels')[sensor.index].get('temp'),
                                cts_temperature=self.temperature(),
                                cts_humidity=self.humidity(),
                                cts_status=self.status(),
                                cts_program=self.program(),
                                hv_status=sensor.hv
                            )
                else:
                    raise StopRequest()
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.showMessage("Done")
        return True

    def rampBias(self, smu, multi):
        """Ramp down SMU voltage to bias voltage."""
        startVoltage = self.currentVoltage() - self.biasVoltage()
        deltaVoltage = startVoltage - self.currentVoltage()
        self.showMessage("Ramping to bias")
        self.showProgress(deltaVoltage, startVoltage)
        step = -self.ivStep() if self.biasVoltage() < self.currentVoltage() else self.ivStep()
        for value in Range(self.currentVoltage(), self.biasVoltage(), step):
            self.setCurrentVoltage(value)
            if not self.stopRequested():
                self.showMessage(f"Ramping to bias ({value:.2f} V)")
                # Set voltage
                smu.source.voltage.level = value
                deltaVoltage = startVoltage - self.currentVoltage()
                self.showProgress(deltaVoltage, startVoltage)
                self.sleep(self.ivDelay())
                totalCurrent = smu.read()[1]
                self.smuReading.emit(dict(U=self.currentVoltage(), I=totalCurrent))
            else:
                raise StopRequest()
        self.showMessage("Done")

    def longterm(self, smu, multi):
        """Run long term measurement."""
        self.showMessage("Measuring...")
        self.itStarted.emit()
        timeBegin = self.time()
        timeEnd = timeBegin + self.itDuration()
        if self.itDuration():
            self.showProgress(0, timeEnd - timeBegin)
        else:
            self.showProgress(0, 0) # progress unknown, infinite run
        t0 = time.time()
        with contextlib.ExitStack() as stack:
            writers = {}
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = make_iso(self.startTime())
                    filename = os.path.join(self.path(), f'it-{name}-{timestamp}.txt')
                    f = open(filename, 'w', newline='')
                    writer = ItWriter(stack.enter_context(f))
                    writer.write_meta(sensor, self.operator(), timestamp, self.ivEndVoltage())
                    writer.write_header()
                    writers[sensor.index] = writer
            while not self.stopRequested():
                self.showMessage("Measuring...")
                currentTime = self.time()
                if self.itDuration():
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                reading = self.scan(smu, multi)
                logger.info("scan reading: %s", reading)
                self.itReading.emit(reading)
                self.smuReading.emit(dict(U=self.currentVoltage(), I=reading.get('I')))
                for sensor in self.sensors():
                    if sensor.enabled:
                        # Time delta since start of IV
                        dt = time.time() - t0
                        writers[sensor.index].write_row(
                            timestamp=dt,
                            voltage=reading.get('U'),
                            current=reading.get('channels')[sensor.index].get('I'),
                            smu_current=reading.get('I'),
                            pt100=reading.get('channels')[sensor.index].get('temp'),
                            cts_temperature=self.temperature(),
                            cts_humidity=self.humidity(),
                            cts_status=self.status(),
                            cts_program=self.program(),
                            hv_status=sensor.hv
                        )
                # Wait...
                interval = self.itInterval()
                interval_step = .25
                while interval > 0:
                    if self.stopRequested():
                        raise StopRequest()
                    self.sleep(interval_step)
                    self.showMessage(f"Next measurement in {interval:.0f} s")
                    interval -= interval_step
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self, smu, multi):
        """Ramp down SMU voltage to zero."""
        minimumStep = 5.0 # quick ramp down minimum step
        zeroVoltage = 0.0
        startVoltage = self.currentVoltage()
        deltaVoltage = startVoltage - self.currentVoltage()
        self.showMessage("Ramping down")
        self.showProgress(deltaVoltage, startVoltage)
        ivStep = max(minimumStep, self.ivStep())
        step = -ivStep if zeroVoltage < self.currentVoltage() else ivStep
        for value in Range(self.currentVoltage(), zeroVoltage, step):
            # Ramp down at any cost to save lives!
            self.setCurrentVoltage(value)
            self.showMessage(f"Ramping to zero ({value:.2f} V)")
            # Set voltage
            smu.source.voltage.level = value
            deltaVoltage = startVoltage - self.currentVoltage()
            self.showProgress(deltaVoltage, startVoltage)
            self.sleep(.25) # value from labview
            self.smuReading.emit(dict(U=self.currentVoltage(), I=None))

        # Diable all shunt box channels
        if self.useShuntBox():
            with self.devices().get('shunt') as shunt:
                shunt.enableAll(False)
                for sensor in self.sensors():
                    sensor.hv = False

        # switch output OFF
        smu.output = 'off'

        self.showMessage("Done")

    def run(self):
        # Open connection to instruments
        with contextlib.ExitStack() as stack:
            smu = stack.enter_context(self.devices().get('smu'))
            multi = stack.enter_context(self.devices().get('multi'))
            try:
                self.setup(smu, multi)
                self.rampUp(smu, multi)
                self.rampBias(smu, multi)
                self.longterm(smu, multi)
            except StopRequest:
                pass
            finally:
                self.rampDown(smu, multi)
                self.showMessage("Stopped")
                self.hideProgress()
