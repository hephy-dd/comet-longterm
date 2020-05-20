from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

from .utils import auto_unit

class StatusWidget(QtWidgets.QWidget, UiLoaderMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()

    def setVoltage(self, voltage):
        """Set current in Volts."""
        self.ui.voltageLineEdit.setText(auto_unit(voltage, 'V', decimals=3))

    def setCurrent(self, current):
        """Set current in Ampere."""
        self.ui.currentLineEdit.setText(auto_unit(current, 'A', decimals=3))

    def setTemperature(self, temperature):
        """Set temperature in Celsius."""
        self.ui.tempLineEdit.setText("{:.1f} °C".format(temperature))

    def setHumidity(self, humidity):
        """Set humidity in percent relative humidity."""
        self.ui.humidLineEdit.setText("{:.1f} %rH".format(humidity))

    def setStatus(self, status, program=None):
        if program is not None:
            self.ui.statusLineEdit.setText(self.tr("{} ({})").format(status, program))
        else:
            self.ui.statusLineEdit.setText(self.tr("{}").format(status))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = StatusWidget()
    w.setVoltage(42)
    w.setCurrent(.42)
    w.setTemperature(4.2)
    w.setHumidity(2.4)
    w.setRunning(False)
    w.show()
    app.exec_()
