from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin, DeviceMixin, ProcessMixin
import random

class CalibrationDialog(QtWidgets.QDialog, UiLoaderMixin, DeviceMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.resistivities = []

    @QtCore.pyqtSlot()
    def onCalibrate(self):
        self.resistivities = []
        for i in range(10):
            self.resistivities.append(random.uniform(450000.,500000.))
        try:
            with self.devices().get('multi') as multi:
                print(multi.resource())
                idn = multi.transport().query('*IDN?')
                print(idn)
        except Exception as e:
            print(e)

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = CalibrationDialog()
    w.exec_()
