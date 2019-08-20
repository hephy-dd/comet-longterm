import time
import random
import logging
from PyQt5 import QtCore

import comet
from comet.drivers.cts import ITC

__all__ = ['EnvironmentWorker', 'MeasurementWorker']

class StopRequest(Exception):
    pass

class FakeData(object):
    """Fake data generator for testing purpose."""

    def __init__(self):
        self.singles = [0.0 for _ in range(10)]
        self.total = 0.0

    def up(self):
        self.singles = [self.singles[i] + random.random() for i in range(10)]
        self.total = sum(self.singles)

    def down(self):
        self.singles = [max(self.singles[i] - random.random(), 0.0) for i in range(10)]
        self.total = sum(self.singles)


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
        self.fake = FakeData()

    def setup(self):
        self.showMessage("Clear buffers")
        self.buff.clear()
        self.showMessage("Setup instruments")
        self.showProgress(0, 3)
        for i in range(3):
            time.sleep(.50)
            self.showProgress(i + 1, 3)
        self.showMessage("Done")
        self.current_voltage = 0.0

    def rampUp(self):
        self.showMessage("Ramping up")
        self.showProgress(self.current_voltage, self.end_voltage)
        for value in comet.Range(self.current_voltage, self.end_voltage, self.step_size):
            self.current_voltage = value
            if self.isGood():
                self.showMessage("Ramping up ({:.2f} V)".format(self.current_voltage))
                # self.smu.setVoltage(self.current_voltage)
                self.showProgress(self.current_voltage, self.end_voltage)
                self.wait(self.step_delay)
                # TODO Reading
                self.fake.up()
                self.buff.append(self.fake.singles, self.fake.total)
            else:
                raise StopRequest()
        self.showProgress(self.current_voltage, self.end_voltage)
        self.showMessage("Done")
        return True

    def rampBias(self):
        step = 5.00
        start_voltage = self.current_voltage - self.bias_voltage
        delta_voltage = self.current_voltage - self.current_voltage
        self.showMessage("Ramping to bias")
        self.showProgress(delta_voltage, start_voltage)
        for value in comet.Range(self.current_voltage, self.bias_voltage, -self.step_size):
            self.current_voltage = value
            if self.isGood():
                self.showMessage("Ramping to bias ({:.2f} V)".format(self.current_voltage))
                # setVoltage(self.current_voltage)
                delta_voltage = self.current_voltage - self.current_voltage
                self.showProgress(delta_voltage, start_voltage)
                # TODO Reading
                self.fake.down()
                self.buff.append(self.fake.singles, self.fake.total)
                time.sleep(.5)
            else:
                raise StopRequest()
        self.showMessage("Done")

    def longterm(self):
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
                if random.random() < 0.1: self.fake.down()
                self.buff.append(self.fake.singles, self.fake.total)
                formatter.write(dict(time=currentTime, total=self.fake.total))
                self.wait(self.measurement_delay)
        self.showProgress(1, 1)
        self.showMessage("Done")

    def rampDown(self):
        zero_voltage = 0.0
        step = 10.0
        start_voltage = self.current_voltage
        delta_voltage = start_voltage - self.current_voltage
        self.showMessage("Ramping down")
        self.showProgress(delta_voltage, start_voltage)
        for value in comet.Range(self.current_voltage, zero_voltage, -self.step_size):
            # Ramp down at any cost to save lives!
            self.current_voltage = value
            delta_voltage = start_voltage - self.current_voltage
            self.showProgress(delta_voltage, start_voltage)
            # TODO Reading
            self.fake.down()
            self.buff.append(self.fake.singles, self.fake.total)
            time.sleep(.15)
        self.showMessage("Done")

    def run(self):
        self.setup()
        try:
            self.rampUp()
            self.rampBias()
            self.longterm()
        except StopRequest:
            pass
        finally:
            self.rampDown()
            self.showMessage("Stopped")
            self.hideProgress()
