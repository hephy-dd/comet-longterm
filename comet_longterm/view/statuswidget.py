from PyQt5 import QtCore
from PyQt5 import QtWidgets

from ..utils import auto_unit


class StatusWidget(QtWidgets.QWidget):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Status")

        self.currentLabel = QtWidgets.QLabel()
        self.currentLabel.setText("Current")

        self.currentLineEdit = QtWidgets.QLineEdit()
        self.currentLineEdit.setMaximumWidth(86)
        self.currentLineEdit.setReadOnly(True)

        self.voltageLabel = QtWidgets.QLabel()
        self.voltageLabel.setText("Voltage")

        self.voltageLineEdit = QtWidgets.QLineEdit()
        self.voltageLineEdit.setMaximumWidth(86)
        self.voltageLineEdit.setReadOnly(True)

        self.smuGroupBox = QtWidgets.QGroupBox()
        self.smuGroupBox.setTitle("SMU Status")

        layout = QtWidgets.QGridLayout(self.smuGroupBox)
        layout.addWidget(self.voltageLabel, 0, 0, 1, 1)
        layout.addWidget(self.voltageLineEdit, 1, 0, 1, 1)
        layout.addWidget(self.currentLabel, 0, 1, 1, 1)
        layout.addWidget(self.currentLineEdit, 1, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            20, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout.addItem(spacerItem, 1, 2, 1, 1)

        self.humidLabel = QtWidgets.QLabel()
        self.humidLabel.setText("Humidity")

        self.humidLineEdit = QtWidgets.QLineEdit()
        self.humidLineEdit.setMaximumWidth(86)
        self.humidLineEdit.setReadOnly(True)

        self.tempLabel = QtWidgets.QLabel()
        self.tempLabel.setText("Temperature")

        self.tempLineEdit = QtWidgets.QLineEdit()
        self.tempLineEdit.setMaximumWidth(86)
        self.tempLineEdit.setReadOnly(True)

        self.statusLabel = QtWidgets.QLabel()
        self.statusLabel.setText("Status (Program)")

        self.statusLineEdit = QtWidgets.QLineEdit()
        self.statusLineEdit.setMaximumWidth(86)
        self.statusLineEdit.setReadOnly(True)

        self.ctsGroupBox = QtWidgets.QGroupBox()
        self.ctsGroupBox.setTitle("Chamber Status")

        layout = QtWidgets.QGridLayout(self.ctsGroupBox)
        layout.addWidget(self.humidLabel, 0, 1, 1, 1)
        layout.addWidget(self.humidLineEdit, 1, 1, 1, 1)
        layout.addWidget(self.tempLabel, 0, 0, 1, 1)
        layout.addWidget(self.tempLineEdit, 1, 0, 1, 1)
        layout.addWidget(self.statusLabel, 0, 2, 1, 1)
        layout.addWidget(self.statusLineEdit, 1, 2, 1, 1)

        spacerItem1 = QtWidgets.QSpacerItem(
            0, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        layout.addItem(spacerItem1, 1, 3, 1, 1)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.smuGroupBox)
        layout.addWidget(self.ctsGroupBox)
        layout.setStretch(0, 2)
        layout.setStretch(1, 3)

    def setVoltage(self, voltage):
        """Set current in Volts."""
        self.voltageLineEdit.setText(auto_unit(voltage, "V", decimals=3))

    def setCurrent(self, current):
        """Set current in Ampere."""
        self.currentLineEdit.setText(auto_unit(current, "A", decimals=3))

    def setCtsEnabled(self, enabled):
        """Set CTS group box enabled."""
        self.ctsGroupBox.setEnabled(enabled)

    def setTemperature(self, temperature):
        """Set temperature in Celsius."""
        self.tempLineEdit.setText("{:.1f} °C".format(temperature))

    def setHumidity(self, humidity):
        """Set humidity in percent relative humidity."""
        self.humidLineEdit.setText("{:.1f} %rH".format(humidity))

    def setStatus(self, status, program=None):
        if program is not None:
            text = self.tr("{} ({})").format(status, program)
        else:
            text = self.tr("{}").format(status)
        self.statusLineEdit.setText(text)
