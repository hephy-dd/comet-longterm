import time

from PyQt5 import QtCore

import comet

__all__ = ['Worker']

class Worker(comet.Worker):

    progressUnknown = QtCore.pyqtSignal(bool)

    def __init__(self):
        super().__init__()
        self.__duration = 0
        self.__itc = None

    def duration(self):
        return self.__duration

    def setDuration(self, duration):
        self.__duration = duration

    def _setup(self):
        self.setMessage("Setup instruments...")
        self.setProgress(0, 3)
        for i in range(3):
            time.sleep(.50)
            self.setProgress(i + 1, 3)
        self.setMessage("Done")

    def _rampUp(self):
        self.setMessage("Ramping up...")
        self.setProgress(0, 10)
        for i in range(10):
            if not self.isGood():
                self.setMessage("Measurement aborted.")
                return False
            time.sleep(1)
            self.setProgress(i + 1, 10)
        self.setMessage("Done")
        return True

    def _rampBias(self):
        self.setMessage("Ramping to bias...")
        self.setProgress(0, 4)
        for i in range(4):
            time.sleep(.25)
            self.setProgress(i + 1, 4)
        self.setMessage("Done")
        return True

    def _longterm(self):
        self.setMessage("Starting longterm measurement")
        timeBegin = time.time()
        timeEnd = timeBegin + self.duration()
        if self.duration():
            self.setProgress(0, timeEnd - timeBegin)
        else:
            self.setProgress(0, 0) # progress unknown, infinite run
        while True:
            currentTime = time.time()
            if not self.isGood():
                self.setMessage("Measurement aborted")
                break
            if self.duration():
                self.setProgress(currentTime - timeBegin, timeEnd - timeBegin)
                if currentTime >= timeEnd:
                    break
        self.setProgress(100, 100)
        self.setMessage("Done")
        return True

    def _rampDown(self):
        self.setMessage("Ramping down...")
        self.setProgress(0, 10)
        for i in range(10):
            time.sleep(.15)
            self.setProgress(i + 1, 10)
        self.setMessage("Done")
        return True

    def run(self):
        self.setMessage("Starting measurement...")
        self._setup()
        if self._rampUp():
            self._longterm()
        self._rampDown()
        self.setMessage("Done")
