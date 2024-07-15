from typing import Optional

from PyQt5 import QtCore, QtWidgets

from ..utils import auto_unit


class StatusWidget(QtWidgets.QWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
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

        smuGroupBoxLayout = QtWidgets.QGridLayout(self.smuGroupBox)
        smuGroupBoxLayout.addWidget(self.voltageLabel, 0, 0, 1, 1)
        smuGroupBoxLayout.addWidget(self.voltageLineEdit, 1, 0, 1, 1)
        smuGroupBoxLayout.addWidget(self.currentLabel, 0, 1, 1, 1)
        smuGroupBoxLayout.addWidget(self.currentLineEdit, 1, 1, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            20, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        smuGroupBoxLayout.addItem(spacerItem, 1, 2, 1, 1)

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

        ctsGroupBoxLayout = QtWidgets.QGridLayout(self.ctsGroupBox)
        ctsGroupBoxLayout.addWidget(self.humidLabel, 0, 1, 1, 1)
        ctsGroupBoxLayout.addWidget(self.humidLineEdit, 1, 1, 1, 1)
        ctsGroupBoxLayout.addWidget(self.tempLabel, 0, 0, 1, 1)
        ctsGroupBoxLayout.addWidget(self.tempLineEdit, 1, 0, 1, 1)
        ctsGroupBoxLayout.addWidget(self.statusLabel, 0, 2, 1, 1)
        ctsGroupBoxLayout.addWidget(self.statusLineEdit, 1, 2, 1, 1)

        spacerItem1 = QtWidgets.QSpacerItem(
            0, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum
        )
        ctsGroupBoxLayout.addItem(spacerItem1, 1, 3, 1, 1)

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.smuGroupBox)
        layout.addWidget(self.ctsGroupBox)
        layout.setStretch(0, 2)
        layout.setStretch(1, 3)

    def setVoltage(self, voltage: float) -> None:
        """Set current in Volts."""
        self.voltageLineEdit.setText(auto_unit(voltage, "V", decimals=3))

    def clearVoltage(self) -> None:
        self.voltageLineEdit.setText("n/a")

    def setCurrent(self, current: float) -> None:
        """Set current in Ampere."""
        self.currentLineEdit.setText(auto_unit(current, "A", decimals=3))

    def clearCurrent(self) -> None:
        self.currentLineEdit.setText("n/a")

    def setCtsEnabled(self, enabled: bool) -> None:
        """Set CTS group box enabled."""
        self.ctsGroupBox.setEnabled(enabled)

    def setTemperature(self, temperature: float) -> None:
        """Set temperature in Celsius."""
        self.tempLineEdit.setText("{:.1f} °C".format(temperature))

    def setHumidity(self, humidity: float) -> None:
        """Set humidity in percent relative humidity."""
        self.humidLineEdit.setText("{:.1f} %rH".format(humidity))

    def setStatus(self, status: str, program: Optional[int] = None) -> None:
        if program is not None:
            text = self.tr("{} ({})").format(status, program)
        else:
            text = self.tr("{}").format(status)
        self.statusLineEdit.setText(text)
