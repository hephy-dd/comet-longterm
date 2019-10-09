import logging
import csv
import contextlib
import datetime
import os

from PyQt5 import QtCore

import pyvisa

from comet import Process, StopRequest, Range
from comet import DeviceMixin

class Writer(object):

    def __init__(self, context):
        self.context = context
        self.writer = csv.writer(context)

    def writeRow(self, *values):
        self.writer.writerow(values)
        self.context.flush()

    def writeHeader(self, name, operator, timestamp, calibration, voltage):
        self.writeRow("HEPHY Vienna longtime It measurement")
        self.writeRow("sensor name: {}".format(name))
        self.writeRow("operator: {}".format(operator))
        self.writeRow("datetime: {}".format(timestamp))
        self.writeRow("calibration [Ohm]: {}".format(calibration))
        self.writeRow("Voltage [V]: {}".format(voltage))
        self.writeRow("")

class IVWriter(Writer):

    pass

class ItWriter(Writer):

    def writeHeader(self, sensor, operator, timestamp, calibration, voltage):
        super().writeHeader(sensor, operator, timestamp, calibration, voltage)
        self.writeRow("timestamp [s]", "current corr [A]", "current meas [A]", "temperature [°C]", "humidity [%rH]", "program [No]")

class EnvironProcess(Process, DeviceMixin):

    reading = QtCore.pyqtSignal(object)
    """Emitted when reading available, contains reading data."""

    interval = 5.0

    def read(self, device):
        """Read environment data from device."""
        temp = device.analogChannel(1)[0]
        humid = device.analogChannel(2)[0]
        program = device.program()
        return dict(time=self.time(), temp=temp, humid=humid, program=program)

    def run(self):
        while not self.stopRequested():
            try:
                with self.devices().get('cts') as cts:
                    while not self.stopRequested():
                        try:
                            reading = self.read(cts)
                            logging.info("CTS reading: %s", reading)
                        except pyvisa.errors.Error as e:
                            logging.error(e)
                            self.failed.emit(e)
                        else:
                            self.reading.emit(reading)
                        self.sleep(self.interval)
            except pyvisa.errors.Error as e:
                logging.error(e)
                self.failed.emit(e)

class MeasProcess(Process, DeviceMixin):

    ivReading = QtCore.pyqtSignal(object)
    """Emitted when IV reading available, contains reading data."""

    itReading = QtCore.pyqtSignal(object)
    """Emitted when It reading available, contains reading data."""

    ivStarted = QtCore.pyqtSignal()
    """Emitted just before IV measurement starts."""

    itStarted = QtCore.pyqtSignal()
    """Emitted just before It measurement starts."""

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
        # check SMU compliance
        totalCurrent = smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.totalCompliance():
            if not self.continueInCompliance():
                raise ValueError("SMU in compliance ({} A)".format(totalCurrent))

        # start measurement scan
        multi.init()
        self.sleep(.500)

        # read buffer
        results = multi.fetch()
        channels = []
        for i, sensor in enumerate(self.sensors()):
            R = sensor.resistivity # ohm, from calibration measurement array
            u = results[i].get('VDC')
            # Calculate sensor current
            current = u / R
            if current > self.singleCompliance():
                sensor.status = sensor.State.COMPL_ERR
                # TODO switch relay off
            channels.append(dict(i=current, u=u, r=R))
        return channels, totalCurrent

    def setup(self, smu, multi):
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

        # set channels to scan
        count = len(self.sensors())
        if count > 10:
            offset = count + 120
            multi.resource().write(':ROUTE:SCAN (@111:120,131:{})'.format(offset))
        else:
            offset = count + 100
            multi.resource().write('ROUTE:SCAN (@101:{})'.format(offset))

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
        self.showMessage("Ramping up")
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.ivStarted.emit()
        with contextlib.ExitStack() as stack:
            writers = []
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime()).strftime('%Y-%m-%dT%H-%M-%S')
                    filename = os.path.join(self.path(), 'IV-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = IVWriter(stack.enter_context(f))
                    writer.writeHeader(name, self.startTime(), self.operator(), sensor.resistivity, self.ivEndVoltage())
                    writers.append(writer)
            for value in Range(self.currentVoltage(), self.ivEndVoltage(), self.ivStep()):
                self.setCurrentVoltage(value)
                if not self.stopRequested():
                    self.showMessage("Ramping up ({:.2f} V)".format(self.currentVoltage()))
                    # Set voltage
                    smu.setVoltage(value)
                    self.showProgress(self.currentVoltage(), self.ivEndVoltage())
                    self.sleep(self.ivInterval())
                    t = self.time()
                    channels, total = self.scan(smu, multi)
                    self.ivReading.emit(dict(time=t, singles=channels, total=total, voltage=self.currentVoltage()))
                    for i, writer in enumerate(writers):
                        # writers[i].writeRow(t, value, current) # timestamp?
                        writer.writeRow(self.currentVoltage(), channels[i].get('i'))
                else:
                    raise StopRequest()
        self.showProgress(self.currentVoltage(), self.ivEndVoltage())
        self.showMessage("Done")
        return True

    def rampBias(self, smu, multi):
        step = 5.00
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
            else:
                raise StopRequest()
        self.showMessage("Done")

    def longterm(self, smu, multi):
        self.showMessage("Measuring...")
        self.itStarted.emit()
        timeBegin = self.time()
        timeEnd = timeBegin + self.itDuration()
        if self.itDuration():
            self.showProgress(0, timeEnd - timeBegin)
        else:
            self.showProgress(0, 0) # progress unknown, infinite run
        with contextlib.ExitStack() as stack:
            writers = []
            for sensor in self.sensors():
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime()).strftime('%Y-%m-%dT%H-%M-%S')
                    filename = os.path.join(self.path(), 'it-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = ItWriter(stack.enter_context(f))
                    writer.writeHeader(name, self.startTime(), self.operator(), sensor.resistivity, self.ivEndVoltage())
                    writers.append(writer)
            while not self.stopRequested():
                self.showMessage("Measuring...")
                currentTime = self.time()
                if self.itDuration():
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                t = self.time()
                channels, total = self.scan(smu, multi)
                self.itReading.emit(dict(time=t, singles=channels, total=total, voltage=self.currentVoltage()))
                for i, writer in enumerate(writers):
                    writer.writeRow(t, channels[i].get('i'), self.temperature(), self.humidity(), self.program())
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
        zeroVoltage = 0.0
        step = 10.0
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
        self.showMessage("Done")

    def run(self):
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
