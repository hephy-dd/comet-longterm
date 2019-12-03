import logging
import csv
import contextlib
import datetime
import os
import traceback

from PyQt5 import QtCore

import pyvisa

from comet import Process, StopRequest, Range
from comet import DeviceMixin

class Writer(object):
    """CSV file writer for IV and It measurements."""

    def __init__(self, context):
        self.context = context
        self.writer = csv.writer(context)

    def writeHeader(self, sensor, operator, timestamp, calibration, voltage):
        self.writer.writerows([
            ["HEPHY Vienna longtime It measurement"],
            ["sensor name: {}".format(sensor.name)],
            ["sensor channel: {}".format(sensor.index)],
            ["operator: {}".format(operator)],
            ["datetime: {}".format(timestamp)],
            ["calibration [Ohm]: {}".format(calibration)],
            ["Voltage [V]: {}".format(voltage)],
            [],
            ["timestamp [s]", "voltage [V]", "current [A]", "temperature [°C]", "humidity [%rH]", "program [Nr]"]
        ])
        self.context.flush()

    def writeRow(self, timestamp, voltage, current, temperature, humidity, program):
        self.writer.writerow([
            format(timestamp, '.3f'),
            format(voltage, 'E'),
            format(current, 'E'),
            format(temperature, 'E'),
            format(humidity, 'E'),
            format(program, 'd')
        ])
        self.context.flush()

class EnvironProcess(Process, DeviceMixin):
    """Environment monitoring process. Polls for temperature, humidity and
    climate chamber program in intervals.
    """

    reading = QtCore.pyqtSignal(object)
    """Emitted when reading available, contains reading data."""

    interval = 5.0

    timeout = 5.0

    failedConnectionAttempts = 0 # HACK

    def read(self, device):
        """Read environment data from device."""
        temp = device.analogChannel(1)[0]
        humid = device.analogChannel(2)[0]
        program = device.program()
        return dict(time=self.time(), temp=temp, humid=humid, program=program)

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
                            logging.info("CTS reading: %s", reading)
                            self.reading.emit(reading)
                        self.sleep(self.interval)
                        self.failedConnectionAttempts = 0
            except Exception as e:
                self.handleException(e)
                self.failedConnectionAttempts += 1
                self.sleep(self.timeout)

class MeasureProcess(Process, DeviceMixin):
    """Long term measurement process, consisting of five stages:

    - reset and setup instruments
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
        self.setCurrentVoltage(0.0)
        self.setTotalCurrent(0.0)
        self.setTemperature(float('nan'))
        self.setHumidity(float('nan'))
        self.setProgram(0)

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

    def totalCurrent(self):
        return self.__totalCurrent

    def setTotalCurrent(self, value):
        self.__totalCurrent = value

    def ivEndVoltage(self):
        return self.__ivEndVoltage

    def setIvEndVoltage(self, value):
        self.__ivEndVoltage = value

    def ivStep(self):
        return self.__ivStep

    def setIvStep(self, value):
        self.__ivStep = value

    def ivInterval(self):
        return self.__ivInterval

    def setIvInterval(self, value):
        self.__ivInterval = value

    def biasVoltage(self,):
        return self.__biasVoltage

    def setBiasVoltage(self, value):
        self.__biasVoltage = value

    def totalCompliance(self):
        return self.__totalCompliance

    def setTotalCompliance(self, value):
        self.__totalCompliance = value

    def singleCompliance(self):
        return self.__singleCompliance

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
        smu.reset()
        multi.reset()
        self.sleep(.500)

    def scan(self, smu, multi):
        """Scan selected channels and return dictionary of readings.

        t:  timestamp
        I:  total SMU current
        U:  current SMU voltage
        channels:  list of channel readings
            index:  index of channel
            I:  current
            U:  voltage
            R:  calibrated resistor value
        """
        # check SMU compliance
        totalCurrent = smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.totalCompliance():
            if not self.continueInCompliance():
                raise ValueError("SMU in compliance ({} A)".format(totalCurrent))

        # start measurement scan
        multi.init()
        self.sleep(.500)

        # read buffer to iterator
        results = iter(multi.fetch())

        channels = {}
        for sensor in self.sensors():
            if sensor.enabled:
                R = sensor.resistivity # ohm, from calibration measurement array
                U = next(results).get('VDC') # pull result
                # Calculate sensor current
                I = U / R
                if I > self.singleCompliance():
                    sensor.status = sensor.State.COMPL_ERR
                    # TODO switch relay off
                channels[sensor.index] = dict(index=sensor.index, I=I, U=U, R=R)
        return dict(time=self.time(), channels=channels, I=totalCurrent, U=self.currentVoltage())

    def setup(self, smu, multi):
        """Setup SMU and Multimeter instruments."""

        self.showMessage("Clear buffers")
        self.setStartTime(self.time())

        for sensor in self.sensors():
            sensor.status = sensor.State.OK

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)
        self.reset(smu, multi)

        logging.info("Multimeter: %s", multi.identification())
        logging.info("Source Unit: %s", smu.identification())
        self.sleep(1.0)

        self.showMessage("Setup multimeter")
        self.showProgress(1, 3)
        multi.resource().write(':FUNC "VOLT:DC", (@101:140)')
        # delete instrument buffer
        multi.resource().write(':TRACE:CLEAR')
        # turn off continous measurements
        multi.resource().write(':INIT:CONT OFF')
        # set trigger source immediately
        multi.resource().write(':TRIG:SOUR IMM')

        # set channels to scan (up to max 10)
        count = len(self.sensors())
        channels = []
        offset = 100
        for sensor in self.sensors():
            if sensor.enabled:
                channels.append(format(offset + sensor.index))
        # ROUTE:SCAN (@101,102,103...)
        multi.resource().write('ROUTE:SCAN (@{})'.format(','.join(channels)))

        multi.resource().write(':TRIG:COUN 1')
        multi.resource().write(':SAMP:COUN {}'.format(count))
        # start scan when triggered
        multi.resource().write(':ROUT:SCAN:TSO IMM')
        # enable scan
        multi.resource().write(':ROUT:SCAN:LSEL INT')

        self.showMessage("Setup source unit")
        self.showProgress(2, 3)
        smu.resource().write('SENS:AVER:TCON REP')
        smu.resource().write('SENS:AVER ON')
        smu.resource().write('ROUT:TERM REAR')
        smu.resource().write(':SOUR:FUNC VOLT')
        smu.enableOutput(False)
        smu.resource().write('SOUR:VOLT:RANG MAX')
        # measure current DC
        smu.resource().write('SENS:FUNC "CURR"')
        # output data format
        smu.resource().write('SENS:CURR:RANG:AUTO 1')
        smu.resource().write('TRIG:CLE')
        smu.resource().write('SENS:AVER:TCON REP')
        smu.resource().write('SENS:AVER OFF')
        smu.resource().write('ROUT:TERM REAR')

        self.sleep(.100) # value from labview

        smu.resource().write('SENS:CURR:PROT:LEV {:E}'.format(self.totalCompliance()))

        # clear voltage
        self.setCurrentVoltage(0.0)
        smu.setVoltage(self.currentVoltage())
        # switch output ON
        smu.enableOutput(True)

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self, smu, multi):
        """Ramp up SMU voltage to end voltage."""
        self.showMessage("Ramping up")
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.ivStarted.emit()
        with contextlib.ExitStack() as stack:
            writers = {}
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime()).strftime('%Y-%m-%dT%H-%M-%S')
                    filename = os.path.join(self.path(), 'IV-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = Writer(stack.enter_context(f))
                    writer.writeHeader(sensor, self.operator(), timestamp, sensor.resistivity, self.ivEndVoltage())
                    writers[sensor.index] = writer
            for value in Range(self.currentVoltage(), self.ivEndVoltage(), self.ivStep()):
                self.setCurrentVoltage(value)
                if not self.stopRequested():
                    self.showMessage("Ramping up ({:.2f} V)".format(self.currentVoltage()))
                    # Set voltage
                    smu.setVoltage(value)
                    self.showProgress(self.currentVoltage(), self.ivEndVoltage())
                    self.sleep(self.ivInterval())
                    reading = self.scan(smu, multi)
                    logging.info("scan reading: %s", reading)
                    self.ivReading.emit(reading)
                    self.smuReading.emit(dict(U=self.currentVoltage(), I=reading.get('I')))
                    for sensor in self.sensors():
                        if sensor.enabled:
                            writers[sensor.index].writeRow(
                                timestamp=reading.get('time'),
                                voltage=reading.get('U'),
                                current=reading.get('channels')[sensor.index].get('I'),
                                temperature=self.temperature(),
                                humidity=self.humidity(),
                                program=self.program()
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
        for value in Range(self.currentVoltage(), self.biasVoltage(), -self.ivStep()):
            self.setCurrentVoltage(value)
            if not self.stopRequested():
                self.showMessage("Ramping to bias ({:.2f} V)".format(self.currentVoltage()))
                # Set voltage
                smu.setVoltage(value)
                deltaVoltage = startVoltage - self.currentVoltage()
                self.showProgress(deltaVoltage, startVoltage)
                self.sleep(2.0) # value from labview
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
        with contextlib.ExitStack() as stack:
            writers = {}
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime()).strftime('%Y-%m-%dT%H-%M-%S')
                    filename = os.path.join(self.path(), 'it-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = Writer(stack.enter_context(f))
                    writer.writeHeader(sensor, self.operator(), timestamp, sensor.resistivity, self.ivEndVoltage())
                    writers[sensor.index] = writer
            while not self.stopRequested():
                self.showMessage("Measuring...")
                currentTime = self.time()
                if self.itDuration():
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                reading = self.scan(smu, multi)
                logging.info("scan reading: %s", reading)
                self.itReading.emit(reading)
                self.smuReading.emit(dict(U=self.currentVoltage(), I=reading.get('I')))
                for sensor in self.sensors():
                    if sensor.enabled:
                        writers[sensor.index].writeRow(
                            timestamp=reading.get('time'),
                            voltage=reading.get('U'),
                            current=reading.get('channels')[sensor.index].get('I'),
                            temperature=self.temperature(),
                            humidity=self.humidity(),
                            program=self.program()
                        )
                # Wait...
                interval = self.itInterval()
                while interval > 0:
                    if self.stopRequested():
                        raise StopRequest()
                    self.sleep(.25)
                    self.showMessage("Next measurement in {:.0f} s".format(interval))
                    interval -= .25
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self, smu, multi):
        """Ramp down SMU voltage to zero."""
        zeroVoltage = 0.0
        startVoltage = self.currentVoltage()
        deltaVoltage = startVoltage - self.currentVoltage()
        self.showMessage("Ramping down")
        self.showProgress(deltaVoltage, startVoltage)
        for value in Range(self.currentVoltage(), zeroVoltage, -self.ivStep()):
            # Ramp down at any cost to save lives!
            self.setCurrentVoltage(value)
            # Set voltage
            smu.setVoltage(value)
            deltaVoltage = startVoltage - self.currentVoltage()
            self.showProgress(deltaVoltage, startVoltage)
            self.sleep(.25) # value from labview
            self.smuReading.emit(dict(U=self.currentVoltage(), I=None))
        self.showMessage("Done")

    def run(self):
        # Open connection to instruments
        with self.devices().get('smu') as smu, \
             self.devices().get('multi') as multi:
            try:
                self.setup(smu, multi)
                self.rampUp(smu, multi)
                self.rampBias(smu, multi)
                self.longterm(smu, multi)
            except StopRequest:
                pass
            finally:
                self.rampDown(smu, multi)
                self.reset(smu, multi)
                self.showMessage("Stopped")
                self.hideProgress()
