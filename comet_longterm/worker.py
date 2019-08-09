import time

from PyQt5 import QtCore

import comet
from slave.transport import Visa, Socket
from comet.drivers.cts import ITC

__all__ = ['EnvironmentWorker', 'MeasurementWorker']

class StopRequest(Exception):
    pass

class EnvironmentWorker(comet.Worker):

    reading = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, interval=1.0):
        super().__init__(parent)
        self.interval = interval
        self.device = ITC(Socket(address=('192.168.100.205', 1080)))

    def run(self):
        while self.isGood():
            t = time.time()
            self.device._transport.write(b'A0')
            temp = float(self.device._transport.read_bytes(14).decode().split(' ')[1])
            self.device._transport.write(b'A1')
            humid = float(self.device._transport.read_bytes(14).decode().split(' ')[1])
            self.reading.emit(dict(time=t, temp=temp, humid=humid))
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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.__itc = None

    def setup(self):
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
        while self.isGood():
            currentTime = time.time()
            if self.duration:
                self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                if currentTime >= timeEnd:
                    break
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
            # Ramp down at any cost to save lifes!
            self.current_voltage = value
            delta_voltage = start_voltage - self.current_voltage
            self.showProgress(delta_voltage, start_voltage)
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
            self.showProgress(0, 1)
