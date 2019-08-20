import time
import random
import logging
from PyQt5 import QtCore

import comet
from comet.drivers.cts import ITC
from comet.drivers.keithley import K2410, K2700

len(self.samples) = 10

__all__ = ['EnvironmentWorker', 'MeasurementWorker']

class StopRequest(Exception):
    pass

# class FakeData(object):
#     """Fake data generator for testing purpose."""
#
#     def __init__(self):
#         self.singles = [0.0 for _ in range(10)]
#         self.total = 0.0
#
#     def up(self):
#         self.singles = [self.singles[i] + random.random() for i in range(10)]
#         self.total = sum(self.singles)
#
#     def down(self):
#         self.singles = [max(self.singles[i] - random.random(), 0.0) for i in range(10)]
#         self.total = sum(self.singles)


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
    total_compliance = 80.0
    single_compliance = 25.0

    duration = 0
    measurement_delay = 1.00

    current_voltage = 0.0

    def __init__(self, samples, buff, parent=None):
        super().__init__(parent)
        self.__itc = None
        self.samples = samples
        self.buff = buff
        # self.fake = FakeData()

    def setup(self, smu, multi):
        self.showMessage("Clear buffers")
        self.buff.clear()

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)
        multi.reset()
        smu.reset()
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
        if len(self.samples) > 10:
            offset = len(self.samples) + 120
            multi.resource().write(':ROUTE:SCAN (@111:120,131:{})'.format(offset))
        else:
            offset = len(self.samples) + 100
            multi.resource().write('ROUTE:SCAN (@101:{})'.format(offset))

        multi.resource().write(':TRIG:COUN 1')
        multi.resource().write(':SAMP:COUN {}'.format(len(self.samples)))
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
        smu.resource().write('OUTP OFF')
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

        smu.resource().write('SENS:CURR:PROT:LEV {:E}'.format(compliance_uamp))

        # clear voltage
        self.current_voltage = 0.0
        smu.resource().write('SOUR:VOLT:LEV {:E}'.format(self.current_voltage))
        # switch output ON
        smu.resource().write('OUTP ON')

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
                smu.resource().write('SOUR:VOLT:LEV {:E}'.format(value))
                self.showProgress(self.current_voltage, self.end_voltage)
                self.wait(self.step_delay)
                # check SMU compliance
                totalCurrent = abs(float(smu.resource().query('READ?')))
                if totalCurrent > total_compliance:
                    raise ValueError(totalCurrent)
                logging.info('SMU current: %s', totalCurrent)
                for sample in self.samples:
                    # start measurement scan
                    multi.resource().write('INIT')
                    time.sleep(.500)
                    # read buffer
                    result = multi.resource().query('FETCH?')
                    # split result
                    R = 470000.0 # ohm, from calibration measurement array
                    u = results.split(',')[sample.index]
                    currents.append(u / R)
                self.buff.append(currents, totalCurrent)
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
                smu.resource().write('SOUR:VOLT:LEV {:E}'.format(value))
                delta_voltage = self.current_voltage - self.current_voltage
                self.showProgress(delta_voltage, start_voltage)
                # TODO Reading
                #self.fake.down()
                #self.buff.append(self.fake.singles, self.fake.total)
                self.wait(2.0) # value from labview
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
        with open('total.csv', 'w') as f:
            formatter = comet.CsvFormatter(f, ('time', 'total'), formats=dict(time='E', total='E'))
            formatter.write_header()
            while self.isGood():
                currentTime = time.time()
                if self.duration:
                    self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                    if currentTime >= timeEnd:
                        break
                # TODO Reading
                #if random.random() < 0.1: self.fake.down()
                #self.buff.append(self.fake.singles, self.fake.total)
                #formatter.write(dict(time=currentTime, total=self.fake.total))
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
            smu.resource().write('SOUR:VOLT:LEV {:E}'.format(value))
            delta_voltage = start_voltage - self.current_voltage
            self.showProgress(delta_voltage, start_voltage)
            # TODO Reading
            #self.fake.down()
            #self.buff.append(self.fake.singles, self.fake.total)
            time.sleep(.20) # value from labview
        smu.reset()
        multi.reset()
        self.showMessage("Done")

    def run(self):
        devices = comet.Settings().devices().get('smu')
        visaLibrary = comet.Settings().visaLibrary()

        with K2410(devices.get('smu'), visaLibrary) as smu:
            with K2700(devices.get('multi'), visaLibrary) as multi:
                self.setup(smu, multi)
                try:
                    self.rampUp(smu, multi)
                    self.rampBias(smu, multi)
                    self.longterm(smu, multi)
                except StopRequest:
                    pass
                finally:
                    self.rampDown(smu, multi)
                    self.showMessage("Stopped")
                    self.hideProgress()
