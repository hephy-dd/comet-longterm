import time
import random
import logging
import os

from PyQt5 import QtCore

import comet
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

__all__ = ['EnvironmentWorker', 'MeasurementWorker']

class StopRequest(Exception):
    pass

class EnvironmentWorker(comet.Worker):

    reading = QtCore.pyqtSignal(object)

    ready = QtCore.pyqtSignal()

    def __init__(self, parent=None, interval=1.0):
        super().__init__(parent)
        self.interval = interval
        self.isReady = False

    def run(self):
        resource = comet.Settings().devices().get('cts')
        visaLibrary = comet.Settings().visaLibrary()
        with ITC(resource, visaLibrary) as device:
            while self.isGood():
                t = time.time()
                temp = device.analogChannel(1)[0]
                humid = device.analogChannel(2)[0]
                self.reading.emit(dict(time=t, temp=temp, humid=humid))
                if not self.isReady:
                    self.isReady = True
                    self.ready.emit()
                self.wait(self.interval)

class MeasurementWorker(comet.Worker):

    operator = None

    end_voltage = 800.0
    step_size = 5.0
    step_delay = 1.00

    bias_voltage = 600.0
    total_compliance = 0.000080
    single_compliance = 0.000025

    duration = 0
    measurement_delay = 1.00

    current_voltage = 0.0

    path = None

    def __init__(self, samples, buff, parent=None):
        super().__init__(parent)
        self.__itc = None
        self.samples = samples
        self.buff = buff
        logging.getLogger('comet').setLevel(logging.INFO)

    def reset(self, smu, multi):
        multi.reset()
        smu.reset()
        time.sleep(.5)

    def scan(self, smu, multi):
        # check SMU compliance
        totalCurrent = smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.total_compliance:
            raise ValueError(totalCurrent)
        # start measurement scan
        multi.init()
        time.sleep(.500)
        # read buffer
        results = multi.fetch()
        currents = []
        for i, sample in enumerate(self.samples):
            R = 470000.0 # ohm, from calibration measurement array
            u = results[i].get('VDC')
            logging.info("U(V): %s", u)
            current = u / R
            if current > self.single_compliance:
                sample.status = sample.State.COMPL_ERR
                # TODO switch relay off
            currents.append(current)

        self.buff.append(currents, totalCurrent)
        return currents, totalCurrent

    def setup(self, smu, multi):
        self.showMessage("Clear buffers")
        self.buff.clear()

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)
        self.reset(smu, multi)
        logging.info("Multimeter: %s", multi.identification())
        logging.info("Source Unit: %s", smu.identification())
        time.sleep(1.0)

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
        count = len(self.samples)
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

        time.sleep(.100) # value from labview

        smu.resource().write('SENS:CURR:PROT:LEV {:E}'.format(self.total_compliance))

        # clear voltage
        self.current_voltage = 0.0
        smu.setVoltage(self.current_voltage)
        # switch output ON
        smu.enableOutput(True)

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self, smu, multi):
        self.showMessage("Ramping up")
        self.showProgress(self.current_voltage, self.end_voltage)
        for value in comet.Range(self.current_voltage, self.end_voltage, self.step_size):
            self.current_voltage = value
            if self.isGood():
                self.showMessage("Ramping up ({:.2f} V)".format(self.current_voltage))
                # Set voltage
                smu.setVoltage(value)
                self.showProgress(self.current_voltage, self.end_voltage)
                self.wait(self.step_delay)
                self.scan(smu, multi)
            else:
                raise StopRequest()
        self.showProgress(self.current_voltage, self.end_voltage)
        self.showMessage("Done")
        return True

    def rampBias(self, smu, multi):
        step = 5.00
        start_voltage = self.current_voltage - self.bias_voltage
        delta_voltage = self.current_voltage - self.current_voltage
        self.showMessage("Ramping to bias")
        self.showProgress(delta_voltage, start_voltage)
        for value in comet.Range(self.current_voltage, self.bias_voltage, -self.step_size):
            self.current_voltage = value
            if self.isGood():
                self.showMessage("Ramping to bias ({:.2f} V)".format(self.current_voltage))
                # Set voltage
                smu.setVoltage(value)
                delta_voltage = self.current_voltage - self.current_voltage
                self.showProgress(delta_voltage, start_voltage)
                self.wait(2.0) # value from labview
                self.scan(smu, multi)
            else:
                raise StopRequest()
        self.showMessage("Done")

    def longterm(self, smu, multi):
        self.showMessage("Measuring...")
        timeBegin = time.time()
        timeEnd = timeBegin + self.duration
        if self.duration:
            self.showProgress(0, timeEnd - timeBegin)
        else:
            self.showProgress(0, 0) # progress unknown, infinite run
        while self.isGood():
            currentTime = time.time()
            if self.duration:
                self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                if currentTime >= timeEnd:
                    break
            self.scan(smu, multi)
            self.wait(self.measurement_delay)
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self, smu, multi):
        zero_voltage = 0.0
        step = 10.0
        start_voltage = self.current_voltage
        delta_voltage = start_voltage - self.current_voltage
        self.showMessage("Ramping down")
        self.showProgress(delta_voltage, start_voltage)
        for value in comet.Range(self.current_voltage, zero_voltage, -self.step_size):
            # Ramp down at any cost to save lives!
            self.current_voltage = value
            # Set voltage
            smu.setVoltage(value)
            delta_voltage = start_voltage - self.current_voltage
            self.showProgress(delta_voltage, start_voltage)
            time.sleep(.25) # value from labview

        smu.reset()
        multi.reset()
        self.showMessage("Done")

    def run(self):
        devices = comet.Settings().devices()
        visaLibrary = comet.Settings().visaLibrary()

        with K2410(devices.get('smu'), visaLibrary) as smu:
            with K2700(devices.get('multi'), visaLibrary) as multi:
                self.setup(smu, multi)
                try:
                    pass
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
