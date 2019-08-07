import time
import sys, os

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
        self.setProgress(0)
        for i in range(3):
            time.sleep(.50)
            self.setProgress(self.progress() + 100/3)
        self.setProgress(100)
        self.setMessage("Done")

    def _rampUp(self):
        self.setMessage("Ramping up...")
        self.setProgress(0)
        for i in range(10):
            if not self.isGood():
                self.setMessage("Measurement aborted.")
                return False
            time.sleep(1)
            self.setProgress(self.progress() + 100/10)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _rampBias(self):
        self.setMessage("Ramping to bias...")
        self.setProgress(0)
        for i in range(4):
            time.sleep(.25)
            self.setProgress(self.progress() + 100/4)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _longterm(self):
        self.setMessage("Longterm measurement...")
        self.setProgress(0)
        timeBegin = time.time()
        timeEnd = timeBegin + self.duration() if self.duration() else None
        if not timeEnd:
            self.progressUnknown.emit(True)
        while True:
            currentTime = time.time()
            if not self.isGood():
                self.setMessage("Measurement aborted.")
                break
            if timeEnd is not None:
                self.setProgress((currentTime-timeBegin)/(self.duration()/100.))
                if currentTime >= timeEnd:
                    break
        if not timeEnd:
            self.progressUnknown.emit(False)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def _rampDown(self):
        self.setMessage("Ramping down...")
        self.setProgress(0)
        for i in range(10):
            time.sleep(.15)
            self.setProgress(self.progress() + 100/10)
        self.setProgress(100)
        self.setMessage("Done")
        return True

    def run(self):
        self.setMessage("Starting measurement...")
        self._setup()
        if self._rampUp():
            self._longterm()
        self._rampDown()
        self.setMessage("Done")
