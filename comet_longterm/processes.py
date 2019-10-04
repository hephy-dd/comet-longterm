import logging
import csv
import contextlib
import datetime
import os

from PyQt5 import QtCore

import pyvisa

from comet import Process, StopRequest, Range
from comet import DeviceMixin

from .sensorswidget import SensorCount

class Writer(object):

    def __init__(self, context):
        self.context = context
        self.writer = csv.writer(context)

    def writeRow(self, *values):
        self.writer.writerow(values)
        self.context.flush()

    def writeHeader(self, name, operator, timestamp, voltage):
        self.writeRow("HEPHY Vienna longtime It measurement")
        self.writeRow("sensor name: {}".format(name))
        self.writeRow("operator: {}".format(operator))
        self.writeRow("datetime: {}".format(timestamp))
        self.writeRow("Voltage [V]: {}".format(voltage))
        self.writeRow("")

class IVWriter(Writer):

    pass

class ItWriter(Writer):

    def writeHeader(self, sensor, operator, timestamp, voltage):
        super().writeHeader(sensor, operator, timestamp, voltage)
        self.writeRow("time", "current corr [A]", "current meas [A]", "temperature [°C]", "humidity [%rH]")

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

class MeasProcess(Process, DeviceMixin):

    ivReading = QtCore.pyqtSignal(object)
    """Emitted when IV reading available, contains reading data."""

    itReading = QtCore.pyqtSignal(object)
    """Emitted when It reading available, contains reading data."""

    ivStarted = QtCore.pyqtSignal()
    """Emitted just before IV measurement starts."""

    itStarted = QtCore.pyqtSignal()
    """Emitted just before It measurement starts."""

    calibration = [470000.0 for _ in range(SensorCount)]
    """Calibrated resistor values for sensors."""

    ivEndVoltage = 800.0
    ivStep = 5.0
    ivInterval = 10.0

    biasVoltage = 600.0
    totalCompliance = 80.0
    singleCompliance = 25.0
    continueInComplienace = False

    itDuration = 0.00
    itInterval = 60.00

    path = None
    operator = None
    sensors = None

    currentVoltage = 0.0

    def setIvEndVoltage(self, value):
        self.ivEndVoltage = value

    def setIvStep(self, value):
        self.ivStep = value

    def setIvInterval(self, value):
        self.ivInterval = value

    def setBiasVoltage(self, value):
        self.biasVoltage = value

    def setTotalCompliance(self, value):
        self.totalCompliance = value

    def setSingleCompliance(self, value):
        self.singleCompliance = value

    def setItDuration(self, value):
        self.itDuration = value

    def setItInterval(self, value):
        self.itInterval = value

    def setEnviron(self, environ):
        self.environ = environ

    def setTemperatur(self, temperature):
        self.humidity

    def setPath(self, value):
        self.path = value

    def setOperator(self, value):
        self.operator = value

    def reset(self, smu, multi):
        smu.reset()
        multi.reset()
        self.sleep(.500)

    def ivScan(self, smu, multi):
        # check SMU compliance
        totalCurrent = smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.totalCompliance:
            if not self.continueInComplienace:
                raise ValueError("SMU in compliance")

        # start measurement scan
        multi.init()
        self.sleep(.500)

        # read buffer
        results = multi.fetch()
        currents = []
        for i, sensor in enumerate(self.sensors):
            R = self.calibration[i] # ohm, from calibration measurement array
            u = results[i].get('VDC')
            #logging.info("U(V): %s", u)
            current = u / R
            if current > self.singleCompliance:
                sensor.status = sensor.State.COMPL_ERR
                # TODO switch relay off
            currents.append(dict(i=current, u=u))
        time = self.time() - self.startTime
        self.ivReading.emit(dict(time=time, singles=currents, total=totalCurrent))
        return time, currents, totalCurrent

    def itScan(self, smu, multi):
        # check SMU compliance
        totalCurrent = smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.totalCompliance:
            if not self.continueInComplienace:
                raise ValueError("SMU in compliance")

        # start measurement scan
        multi.init()
        self.sleep(.500)

        # read buffer
        results = multi.fetch()
        currents = []
        for i, sensor in enumerate(self.sensors):
            R = self.calibration[i] # ohm, from calibration measurement array
            u = results[i].get('VDC')
            logging.info("U(V): %s", u)
            current = u / R
            if current > self.singleCompliance:
                sensor.status = sensor.State.COMPL_ERR
                # TODO switch relay off
            currents.append(dict(i=current, u=u))

        time = self.time() - self.startTime
        self.itReading.emit(dict(time=time, singles=currents, total=totalCurrent))
        return time, currents, totalCurrent

    def setup(self, smu, multi):
        self.showMessage("Clear buffers")
        self.startTime = self.time()

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
        count = len(self.sensors)
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

        smu.resource().write('SENS:CURR:PROT:LEV {:E}'.format(self.totalCompliance))

        # clear voltage
        self.currentVoltage = 0.0
        smu.setVoltage(self.currentVoltage)
        # switch output ON
        smu.enableOutput(True)

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self, smu, multi):
        self.showMessage("Ramping up")
        self.showProgress(self.currentVoltage, self.ivEndVoltage)
        with contextlib.ExitStack() as stack:
            writers = []
            for sensor in self.sensors:
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime).strftime('%Y-%m-%dT%H-%M')
                    filename = os.path.join(self.path, 'IV-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = IVWriter(stack.enter_context(f))
                    writer.writeHeader(name, self.startTime, self.operator, self.ivEndVoltage)
                    writers.append(writer)
            for value in Range(self.currentVoltage, self.ivEndVoltage, self.ivStep):
                self.currentVoltage = value
                if not self.stopRequested():
                    self.showMessage("Ramping up ({:.2f} V)".format(self.currentVoltage))
                    # Set voltage
                    smu.setVoltage(value)
                    self.showProgress(self.currentVoltage, self.ivEndVoltage)
                    self.sleep(self.ivStep)
                    t, currents, total = self.ivScan(smu, multi)
                    for i, writer in enumerate(writers):
                        # writers[i].writeRow([t, value, current]) # timestamp?
                        writer.writeRow([self.currentVoltage, currents[i]])
                else:
                    raise StopRequest()
        self.showProgress(self.currentVoltage, self.ivEndVoltage)
        self.showMessage("Done")
        return True

    def rampBias(self, smu, multi):
        step = 5.00
        startVoltage = self.currentVoltage - self.biasVoltage
        deltaVoltage = self.currentVoltage - self.currentVoltage
        self.showMessage("Ramping to bias")
        self.showProgress(deltaVoltage, startVoltage)
        for value in Range(self.currentVoltage, self.biasVoltage, -self.ivStep):
            self.currentVoltage = value
            if not self.stopRequested():
                self.showMessage("Ramping to bias ({:.2f} V)".format(self.currentVoltage))
                # Set voltage
                smu.setVoltage(value)
                deltaVoltage = self.currentVoltage - self.currentVoltage
                self.showProgress(deltaVoltage, startVoltage)
                self.sleep(2.0) # value from labview
            else:
                raise StopRequest()
        self.showMessage("Done")

    def longterm(self, smu, multi):
        self.showMessage("Measuring...")
        timeBegin = self.time()
        timeEnd = timeBegin + self.itDuration * 3600 # sec
        if self.itDuration:
            self.showProgress(0, timeEnd - timeBegin)
        else:
            self.showProgress(0, 0) # progress unknown, infinite run
        with contextlib.ExitStack() as stack:
            writers = []
            for sensor in self.sensors:
                if sensor.enabled:
                    name = sensor.name
                    timestamp = datetime.datetime.utcfromtimestamp(self.startTime).strftime('%Y-%m-%dT%H-%M')
                    filename = os.path.join(self.path, 'it-{}-{}.txt'.format(name, timestamp))
                    f = open(filename, 'w', newline='')
                    writer = ItWriter(stack.enter_context(f))
                    writer.writeHeader(name, self.startTime, self.operator, self.ivEndVoltage)
                    writers.append(writer)
            while not self.stopRequested():
                currentTime = self.time()
                if self.itDuration:
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                t, currents, total = self.itScan()
                for i, writer in enumerate(writers):
                    writer.writeRow([t, currents[i], self.temperature, self.humidity])
                self.sleep(self.itInterval)
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self, smu, multi):
        zeroVoltage = 0.0
        step = 10.0
        startVoltage = self.currentVoltage
        deltaVoltage = startVoltage - self.currentVoltage
        self.showMessage("Ramping down")
        self.showProgress(deltaVoltage, startVoltage)
        for value in Range(self.currentVoltage, zeroVoltage, -self.ivStep):
            # Ramp down at any cost to save lives!
            self.currentVoltage = value
            # Set voltage
            smu.setVoltage(value)
            deltaVoltage = startVoltage - self.currentVoltage
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
