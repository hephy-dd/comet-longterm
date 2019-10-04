from PyQt5 import QtCore

from comet import Process, StopRequest

class EnvironProcess(Process):

    reading = QtCore.pyqtSignal(object)

    interval = 5.0

    def read(self, device):
        """Read environment data from device."""
        temp = device.analogChannel(1)[0]
        humid = device.analogChannel(2)[0]
        return dict(time=time.time(), temp=temp, humid=humid, program=False)

    def run(self):
        with self.devices().get('cts') as cts:
            while not self.stopRequested():
                try:
                    reading = self.read(cts)
                except Exception as e:
                    self.failed.emit()
                else:
                    self.reading.emit(reading)
                self.sleep(self.interval)

class MeasProcess(Process):

    ivReading = QtCore.pyqtSignal(object)
    itReading = QtCore.pyqtSignal(object)

    ivStarted = QtCore.pyqtSignal()
    itStarted = QtCore.pyqtSignal()

    calibration = [470000.0 for _ in range(10)]

    endVoltage = 800.00
    stepSize = 5.00
    ivInterval = 10.0

    measInterval = 60.0

    currentVoltage = 0.00

    def reset(self):
        self.multi.reset()
        self.smu.reset()
        time.sleep(.5)

    def scan(self):
        # check SMU compliance
        totalCurrent = self.smu.read()[1]
        logging.info('SMU current (A): %s', totalCurrent)
        if totalCurrent > self.total_compliance:
            raise ValueError(totalCurrent)
        # start measurement scan
        self.multi.init()
        time.sleep(.500)
        # read buffer
        results = self.multi.fetch()
        currents = []
        for i, sample in enumerate(self.samples):
            R = self.calibration[i] # ohm, from calibration measurement array
            u = results[i].get('VDC')
            logging.info("U(V): %s", u)
            current = u / R
            if current > self.single_compliance:
                sample.status = sample.State.COMPL_ERR
                # TODO switch relay off
            currents.append(current)
        t = time.time() - self.startTime
        self.reading.emit(dict(time=t, singles=currents, total=totalCurrent))
        return t, currents, totalCurrent

    def setup(self):
        self.showMessage("Clear buffers")
        self.clear.emit()
        self.startTime = time.time()

        self.showMessage("Reset instruments")
        self.showProgress(0, 3)
        self.reset()
        logging.info("Multimeter: %s", self.multi.identification())
        logging.info("Source Unit: %s", self.smu.identification())
        time.sleep(1.0)

        self.showMessage("Setup multimeter")
        self.showProgress(1, 3)
        self.multi.resource().write(':FUNC "VOLT:DC", (@101:140)')
        # delete instrument buffer
        self.multi.resource().write(':TRACE:CLEAR')
        # turn off continous measurements
        self.multi.resource().write(':INIT:CONT OFF')
        # set trigger source immediately
        self.multi.resource().write(':TRIG:SOUR IMM')

        # set channels to scan
        count = len(self.samples)
        if count > 10:
            offset = count + 120
            self.multi.resource().write(':ROUTE:SCAN (@111:120,131:{})'.format(offset))
        else:
            offset = count + 100
            self.multi.resource().write('ROUTE:SCAN (@101:{})'.format(offset))

        self.multi.resource().write(':TRIG:COUN 1')
        self.multi.resource().write(':SAMP:COUN {}'.format(count))
        # start scan when triggered
        self.multi.resource().write(':ROUT:SCAN:TSO IMM')
        # enable scan
        self.multi.resource().write(':ROUT:SCAN:LSEL INT')

        self.showMessage("Setup source unit")
        self.showProgress(2, 3)
        self.smu.resource().write('SENS:AVER:TCON REP')
        self.smu.resource().write('SENS:AVER ON')
        self.smu.resource().write('ROUT:TERM REAR')
        self.smu.resource().write(':SOUR:FUNC VOLT')
        self.smu.enableOutput(False)
        self.smu.resource().write('SOUR:VOLT:RANG MAX')
        # measure current DC
        self.smu.resource().write('SENS:FUNC "CURR"')
        # output data format
        self.smu.resource().write('SENS:CURR:RANG:AUTO 1')
        self.smu.resource().write('TRIG:CLE')
        self.smu.resource().write('SENS:AVER:TCON REP')
        self.smu.resource().write('SENS:AVER OFF')
        self.smu.resource().write('ROUT:TERM REAR')

        time.sleep(.100) # value from labview

        self.smu.resource().write('SENS:CURR:PROT:LEV {:E}'.format(self.total_compliance))

        # clear voltage
        self.current_voltage = 0.0
        self.smu.setVoltage(self.current_voltage)
        # switch output ON
        self.smu.enableOutput(True)

        self.showProgress(3, 3)
        self.showMessage("Done")

    def rampUp(self):
        self.showMessage("Ramping up")
        self.showProgress(self.current_voltage, self.end_voltage)
        for value in comet.Range(self.current_voltage, self.end_voltage, self.step_size):
            self.current_voltage = value
            if not self.stopRequested():
                self.showMessage("Ramping up ({:.2f} V)".format(self.current_voltage))
                # Set voltage
                self.smu.setVoltage(value)
                self.showProgress(self.current_voltage, self.end_voltage)
                self.wait(self.step_delay)
                t, currents, total = self.scan()
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
            if not self.stopRequested():
                self.showMessage("Ramping to bias ({:.2f} V)".format(self.current_voltage))
                # Set voltage
                self.smu.setVoltage(value)
                delta_voltage = self.current_voltage - self.current_voltage
                self.showProgress(delta_voltage, start_voltage)
                self.wait(2.0) # value from labview
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
        while not self.stopRequested():
            currentTime = time.time()
            if self.duration:
                self.showProgress(currentTime - timeBegin, timeEnd - timeBegin)
                if currentTime >= timeEnd:
                    break
            t, currents, total = self.scan()
            t = time.time() - timeBegin
            for i, current in enumerate(currents):
                writer = csv.writer(files[i])
                writer.writerow([t, current, self.temperature, self.humidity])
                files[i].flush()
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
            # Set voltage
            self.smu.setVoltage(value)
            delta_voltage = start_voltage - self.current_voltage
            self.showProgress(delta_voltage, start_voltage)
            time.sleep(.25) # value from labview
        self.showMessage("Done")

    def run(self):
        try:
            self.setup()
            self.rampUp()
            self.rampBias()
            self.longterm()
        except StopRequest:
            pass
        finally:
            self.rampDown()
            self.reset()
            self.showMessage("Stopped")
            self.hideProgress()
