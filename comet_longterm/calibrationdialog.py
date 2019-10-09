from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin, DeviceMixin, ProcessMixin
import random

class CalibrationDialog(QtWidgets.QDialog, UiLoaderMixin, DeviceMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.resistivity = []

    @QtCore.pyqtSlot()
    def onCalibrate(self):
        self.resistivity = []
        for i in range(10):
            # TODO
            self.resistivity.append(random.uniform(450000.,500000.))
        try:
            with self.devices().get('multi') as multi:
                idn = multi.resource().query('*IDN?')
                print(idn)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, self.tr("Error"), format(e))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = CalibrationDialog()
    w.exec_()
