import logging

from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

from .utils import auto_unit

logger = logging.getLogger(__name__)

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
