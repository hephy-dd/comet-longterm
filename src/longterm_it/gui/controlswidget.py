import os
from typing import Optional

from PyQt5 import QtCore, QtWidgets


class ControlsWidget(QtWidgets.QWidget):

    started = QtCore.pyqtSignal()
    stopRequest = QtCore.pyqtSignal()
    halted = QtCore.pyqtSignal()

    useShuntBoxChanged = QtCore.pyqtSignal(bool)
    ivEndVoltageChanged = QtCore.pyqtSignal(float)
    ivStepChanged = QtCore.pyqtSignal(float)
    ivDelayChanged = QtCore.pyqtSignal(float)
    biasVoltageChanged = QtCore.pyqtSignal(float)
    totalComplianceChanged = QtCore.pyqtSignal(float)
    singleComplianceChanged = QtCore.pyqtSignal(float)
    continueInComplianceChanged = QtCore.pyqtSignal(bool)
    itDurationChanged = QtCore.pyqtSignal(float)
    itIntervalChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Controls")

        # Controls

        self.startPushButton = QtWidgets.QPushButton()
        self.startPushButton.setText("&Start")
        self.startPushButton.setStatusTip("Start a new measurement.")
        self.startPushButton.setCheckable(True)
        self.startPushButton.setChecked(False)

        self.stopPushButton = QtWidgets.QPushButton()
        self.stopPushButton.setText("Sto&p")
        self.stopPushButton.setStatusTip("Stop current measurement.")
        self.stopPushButton.setEnabled(False)
        self.stopPushButton.setFixedSize(140, 100)
        self.stopPushButton.setCheckable(True)
        self.stopPushButton.setChecked(True)

        self.ctsCheckBox = QtWidgets.QCheckBox()
        self.ctsCheckBox.setText("Use &Chamber")
        self.ctsCheckBox.setToolTip("Use CTS climate chamber for measurements.")
        self.ctsCheckBox.setStatusTip("Use CTS climate chamber for measurements.")
        self.ctsCheckBox.setCheckable(True)
        self.ctsCheckBox.setChecked(True)

        self.shuntBoxCheckBox = QtWidgets.QCheckBox()
        self.shuntBoxCheckBox.setText("Use Shunt&Box")
        self.shuntBoxCheckBox.setToolTip("Use HEPHY shunt box in measurements.")
        self.shuntBoxCheckBox.setStatusTip("Use HEPHY shunt box in measurements.")
        self.shuntBoxCheckBox.setCheckable(True)
        self.shuntBoxCheckBox.setChecked(True)

        self.controlLayout = QtWidgets.QVBoxLayout()
        self.controlLayout.addWidget(self.startPushButton)
        self.controlLayout.addWidget(self.stopPushButton)
        self.controlLayout.addWidget(self.ctsCheckBox)
        self.controlLayout.addWidget(self.shuntBoxCheckBox)
        self.controlLayout.addStretch()

        # General tab

        self.biasComplianceLabel = QtWidgets.QLabel()
        self.biasComplianceLabel.setText("Bias Voltage")

        self.totalComplianceSpinBox = QtWidgets.QDoubleSpinBox()
        self.totalComplianceSpinBox.setToolTip("SMU compliance.")
        self.totalComplianceSpinBox.setDecimals(3)
        self.totalComplianceSpinBox.setMinimum(1.0)
        self.totalComplianceSpinBox.setMaximum(100000.0)
        self.totalComplianceSpinBox.setValue(80.0)
        self.totalComplianceSpinBox.setSuffix(" uA")

        self.singleComplianceSpinBox = QtWidgets.QDoubleSpinBox()
        self.singleComplianceSpinBox.setDecimals(3)
        self.singleComplianceSpinBox.setMinimum(0.001)
        self.singleComplianceSpinBox.setMaximum(1000000.0)
        self.singleComplianceSpinBox.setValue(25.0)
        self.singleComplianceSpinBox.setSuffix(" uA")

        self.continueInComplianceCheckBox = QtWidgets.QCheckBox()
        self.continueInComplianceCheckBox.setText("&Continue in Compl.")
        self.continueInComplianceCheckBox.setToolTip(
            "Continue measurement when SMU in compliance."
        )
        self.continueInComplianceCheckBox.setStatusTip(
            "Continue measurement when SMU in compliance."
        )
        self.continueInComplianceCheckBox.setChecked(True)

        self.complGroupBox = QtWidgets.QGroupBox()
        self.complGroupBox.setTitle("Compliance")
        self.complGroupBox.setMinimumWidth(140)

        self.totalComplianceLabel = QtWidgets.QLabel()
        self.totalComplianceLabel.setText("Total Compliance")

        self.singleComplianceLabel = QtWidgets.QLabel()
        self.singleComplianceLabel.setText("Single Compliance")

        complGroupBoxLayout = QtWidgets.QGridLayout(self.complGroupBox)
        complGroupBoxLayout.addWidget(self.totalComplianceLabel, 2, 0, 1, 1)
        complGroupBoxLayout.addWidget(self.totalComplianceSpinBox, 3, 0, 1, 1)
        complGroupBoxLayout.addWidget(self.singleComplianceLabel, 4, 0, 1, 1)
        complGroupBoxLayout.addWidget(self.singleComplianceSpinBox, 5, 0, 1, 1)
        complGroupBoxLayout.addWidget(self.continueInComplianceCheckBox, 6, 0, 1, 1)

        spacerItem1 = QtWidgets.QSpacerItem(
            20, 12, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        complGroupBoxLayout.addItem(spacerItem1, 7, 0, 1, 1)

        self.ivEndVoltageLabel = QtWidgets.QLabel()
        self.ivEndVoltageLabel.setText("End Voltage")

        self.ivEndVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.ivEndVoltageSpinBox.setDecimals(1)
        self.ivEndVoltageSpinBox.setMinimum(-1000.0)
        self.ivEndVoltageSpinBox.setMaximum(1000.0)
        self.ivEndVoltageSpinBox.setValue(800.0)
        self.ivEndVoltageSpinBox.setSuffix(" V")

        self.ivStepLabel = QtWidgets.QLabel()
        self.ivStepLabel.setText("Step")

        self.ivStepSpinBox = QtWidgets.QDoubleSpinBox()
        self.ivStepSpinBox.setDecimals(1)
        self.ivStepSpinBox.setMinimum(0.1)
        self.ivStepSpinBox.setMaximum(1000.0)
        self.ivStepSpinBox.setValue(5.0)
        self.ivStepSpinBox.setSuffix(" V")

        self.ivDelayLabel = QtWidgets.QLabel()
        self.ivDelayLabel.setText("Meas. Delay")

        self.ivDelaySpinBox = QtWidgets.QDoubleSpinBox()
        self.ivDelaySpinBox.setDecimals(0)
        self.ivDelaySpinBox.setMinimum(1.0)
        self.ivDelaySpinBox.setMaximum(3600000.0)
        self.ivDelaySpinBox.setValue(1000.0)
        self.ivDelaySpinBox.setSuffix(" ms")

        self.ivGroupBox = QtWidgets.QGroupBox()
        self.ivGroupBox.setTitle("IV Ramp")
        self.ivGroupBox.setMinimumWidth(140)

        ivGroupBoxLayout = QtWidgets.QGridLayout(self.ivGroupBox)
        ivGroupBoxLayout.addWidget(self.ivEndVoltageLabel, 0, 0, 1, 1)
        ivGroupBoxLayout.addWidget(self.ivEndVoltageSpinBox, 1, 0, 1, 1)
        ivGroupBoxLayout.addWidget(self.ivStepLabel, 2, 0, 1, 1)
        ivGroupBoxLayout.addWidget(self.ivStepSpinBox, 3, 0, 1, 1)
        ivGroupBoxLayout.addWidget(self.ivDelayLabel, 4, 0, 1, 1)
        ivGroupBoxLayout.addWidget(self.ivDelaySpinBox, 5, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        ivGroupBoxLayout.addItem(spacerItem, 6, 0, 1, 1)

        self.biasVoltageSpinBox = QtWidgets.QDoubleSpinBox()
        self.biasVoltageSpinBox.setDecimals(1)
        self.biasVoltageSpinBox.setMinimum(-1000.0)
        self.biasVoltageSpinBox.setMaximum(1000.0)
        self.biasVoltageSpinBox.setValue(600.0)
        self.biasVoltageSpinBox.setSuffix(" V")

        self.itDurationLabel = QtWidgets.QLabel()
        self.itDurationLabel.setText("Meas. Duration")

        self.itDurationSpinBox = QtWidgets.QDoubleSpinBox()
        self.itDurationSpinBox.setDecimals(1)
        self.itDurationSpinBox.setMaximum(8544.0)
        self.itDurationSpinBox.setValue(0.0)
        self.itDurationSpinBox.setSpecialValueText("Unlimited")
        self.itDurationSpinBox.setSuffix(" h")

        self.itIntervalLabel = QtWidgets.QLabel()
        self.itIntervalLabel.setText("Meas. Interval")

        self.itIntervalSpinBox = QtWidgets.QDoubleSpinBox()
        self.itIntervalSpinBox.setDecimals(0)
        self.itIntervalSpinBox.setMinimum(1.0)
        self.itIntervalSpinBox.setMaximum(3600.0)
        self.itIntervalSpinBox.setValue(60.0)
        self.itIntervalSpinBox.setSuffix(" s")

        self.itGroupBox = QtWidgets.QGroupBox()
        self.itGroupBox.setTitle("It Longterm")
        self.itGroupBox.setMinimumWidth(140)

        itGroupBoxLayout = QtWidgets.QGridLayout(self.itGroupBox)
        itGroupBoxLayout.addWidget(self.biasComplianceLabel, 0, 0, 1, 1)
        itGroupBoxLayout.addWidget(self.biasVoltageSpinBox, 1, 0, 1, 1)
        itGroupBoxLayout.addWidget(self.itDurationLabel, 2, 0, 1, 1)
        itGroupBoxLayout.addWidget(self.itDurationSpinBox, 3, 0, 1, 1)
        itGroupBoxLayout.addWidget(self.itIntervalLabel, 4, 0, 1, 1)
        itGroupBoxLayout.addWidget(self.itIntervalSpinBox, 5, 0, 1, 1)
        spacerItem = QtWidgets.QSpacerItem(
            20, 89, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding
        )
        itGroupBoxLayout.addItem(spacerItem, 6, 0, 1, 1)

        self.generalWidget = QtWidgets.QWidget()

        generalWidgetLayout = QtWidgets.QHBoxLayout(self.generalWidget)
        generalWidgetLayout.addWidget(self.complGroupBox)
        generalWidgetLayout.addWidget(self.ivGroupBox)
        generalWidgetLayout.addWidget(self.itGroupBox)
        generalWidgetLayout.setStretch(0, 1)
        generalWidgetLayout.setStretch(1, 1)
        generalWidgetLayout.setStretch(2, 1)

        self.smuWidget = SMUWidget()

        self.dmmWidget = DMMWidget()

        # Tab widget

        self.tabWidget = QtWidgets.QTabWidget()
        self.tabWidget.addTab(self.generalWidget, "General")
        self.tabWidget.addTab(self.smuWidget, "SMU")
        self.tabWidget.addTab(self.dmmWidget, "Multimeter")
        self.tabWidget.setCurrentIndex(0)

        # Operator

        self.operatorComboBox = QtWidgets.QComboBox()
        self.operatorComboBox.setEditable(True)
        self.operatorComboBox.setDuplicatesEnabled(False)

        self.operatorGroupBox = QtWidgets.QGroupBox()
        self.operatorGroupBox.setTitle("Operator")
        self.operatorGroupBox.setMaximumWidth(220)

        operatorGroupBoxLayout = QtWidgets.QHBoxLayout(self.operatorGroupBox)
        operatorGroupBoxLayout.addWidget(self.operatorComboBox)

        # Output path

        self.pathComboBox = QtWidgets.QComboBox()
        self.pathComboBox.setEditable(True)

        self.selectPathPushButton = QtWidgets.QToolButton()
        self.selectPathPushButton.setText("...")

        self.pathGroupBox = QtWidgets.QGroupBox()
        self.pathGroupBox.setTitle("Output Path")

        pathGroupBoxLayout = QtWidgets.QHBoxLayout(self.pathGroupBox)
        pathGroupBoxLayout.addWidget(self.pathComboBox)
        pathGroupBoxLayout.addWidget(self.selectPathPushButton)

        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.addWidget(self.operatorGroupBox)
        self.horizontalLayout.addWidget(self.pathGroupBox)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addLayout(self.controlLayout, 0, 0, 1, 1)
        layout.addWidget(self.tabWidget, 0, 1, 1, 1)
        layout.addLayout(self.horizontalLayout, 2, 0, 1, 2)
        layout.setRowStretch(1, 1)

        self.setTabOrder(self.startPushButton, self.stopPushButton)
        self.setTabOrder(self.stopPushButton, self.totalComplianceSpinBox)
        self.setTabOrder(self.totalComplianceSpinBox, self.singleComplianceSpinBox)
        self.setTabOrder(
            self.singleComplianceSpinBox, self.continueInComplianceCheckBox
        )
        self.setTabOrder(self.continueInComplianceCheckBox, self.ivEndVoltageSpinBox)
        self.setTabOrder(self.ivEndVoltageSpinBox, self.ivStepSpinBox)
        self.setTabOrder(self.ivStepSpinBox, self.ivDelaySpinBox)
        self.setTabOrder(self.ivDelaySpinBox, self.biasVoltageSpinBox)
        self.setTabOrder(self.biasVoltageSpinBox, self.itDurationSpinBox)
        self.setTabOrder(self.itDurationSpinBox, self.itIntervalSpinBox)
        self.setTabOrder(self.itIntervalSpinBox, self.operatorComboBox)
        self.setTabOrder(self.operatorComboBox, self.pathComboBox)
        self.setTabOrder(self.pathComboBox, self.selectPathPushButton)

        # Setup signals
        self.startPushButton.clicked.connect(self.onStart)
        self.stopPushButton.clicked.connect(self.onStop)
        self.shuntBoxCheckBox.toggled.connect(
            lambda: self.useShuntBoxChanged.emit(self.isShuntBoxEnabled())
        )
        self.ivEndVoltageSpinBox.editingFinished.connect(
            lambda: self.ivEndVoltageChanged.emit(self.ivEndVoltage())
        )
        self.ivEndVoltageSpinBox.editingFinished.connect(self.onIvEndVoltageChanged)
        self.ivStepSpinBox.editingFinished.connect(
            lambda: self.ivStepChanged.emit(self.ivStep())
        )
        self.ivDelaySpinBox.editingFinished.connect(
            lambda: self.ivDelayChanged.emit(self.ivDelay())
        )
        self.biasVoltageSpinBox.editingFinished.connect(
            lambda: self.biasVoltageChanged.emit(self.biasVoltage())
        )
        self.totalComplianceSpinBox.editingFinished.connect(
            lambda: self.totalComplianceChanged.emit(self.totalCompliance())
        )
        self.totalComplianceSpinBox.editingFinished.connect(
            self.onTotalComplianceChanged
        )
        self.singleComplianceSpinBox.editingFinished.connect(
            lambda: self.singleComplianceChanged.emit(self.singleCompliance())
        )
        self.continueInComplianceCheckBox.toggled.connect(
            lambda: self.continueInComplianceChanged.emit(self.continueInCompliance())
        )
        self.itDurationSpinBox.editingFinished.connect(
            lambda: self.itDurationChanged.emit(self.itDuration())
        )
        self.itIntervalSpinBox.editingFinished.connect(
            lambda: self.itIntervalChanged.emit(self.itInterval())
        )
        self.selectPathPushButton.clicked.connect(self.onSelectPath)

        # Syncronize limits
        self.onIvEndVoltageChanged()
        self.onTotalComplianceChanged()

    def onIvEndVoltageChanged(self) -> None:
        """Syncronize bias voltage and step with end voltage limit."""
        bias = self.biasVoltageSpinBox.value()
        if self.ivEndVoltage() < 0:
            self.biasVoltageSpinBox.setMinimum(self.ivEndVoltage())
            self.biasVoltageSpinBox.setMaximum(0)
            self.biasVoltageSpinBox.setValue(-abs(bias))
        else:
            self.biasVoltageSpinBox.setMinimum(0)
            self.biasVoltageSpinBox.setMaximum(self.ivEndVoltage())
            self.biasVoltageSpinBox.setValue(abs(bias))
        self.ivStepSpinBox.setMaximum(abs(self.ivEndVoltage()))

    def onTotalComplianceChanged(self) -> None:
        """Syncronize total/single compliance limit."""
        self.singleComplianceSpinBox.setMaximum(
            self.totalCompliance() * 1000 * 1000
        )  # in uA

    def isEnvironEnabled(self) -> bool:
        """Returns True if use CTS is checked."""
        return self.ctsCheckBox.isChecked()

    def setEnvironEnabled(self, value: bool) -> None:
        """Set use CTS enabled."""
        self.ctsCheckBox.setChecked(value)

    def isShuntBoxEnabled(self) -> bool:
        """Returns True if use shunt box is checked."""
        return self.shuntBoxCheckBox.isChecked()

    def setShuntBoxEnabled(self, value: bool) -> None:
        """Set shunt box enabled."""
        self.shuntBoxCheckBox.setChecked(value)

    def ivEndVoltage(self) -> float:
        """Returns IV ramp up end voltage in volts."""
        return self.ivEndVoltageSpinBox.value()

    def setIvEndVoltage(self, value: float) -> None:
        """Set IV ramp up end voltage in volts."""
        self.ivEndVoltageSpinBox.setValue(value)

    def ivStep(self) -> float:
        """Returns IV ramp up step size in volts."""
        return self.ivStepSpinBox.value()

    def setIvStep(self, value: float) -> None:
        """Set IV ramp up step size in volts."""
        self.ivStepSpinBox.setValue(value)

    def ivDelay(self) -> float:
        """Returns IV measurement interval in seconds."""
        return self.ivDelaySpinBox.value() / 1000.0

    def setIvDelay(self, value: float) -> None:
        """Set IV measurement interval in seconds."""
        self.ivDelaySpinBox.setValue(value * 1000.0)

    def biasVoltage(self) -> float:
        """Returns It bias voltage in volts."""
        return self.biasVoltageSpinBox.value()

    def setBiasVoltage(self, value: float) -> None:
        """Set It bias voltage in volts."""
        self.biasVoltageSpinBox.setValue(value)

    def totalCompliance(self) -> float:
        """Returns total compliance in Ampere."""
        return self.totalComplianceSpinBox.value() / 1000 / 1000

    def setTotalCompliance(self, value: float) -> None:
        """Set total compliance in Ampere."""
        self.totalComplianceSpinBox.setValue(value * 1000 * 1000)

    def singleCompliance(self) -> float:
        """Returns single compliance in Ampere."""
        return self.singleComplianceSpinBox.value() / 1000 / 1000

    def setSingleCompliance(self, value: float) -> None:
        """Set single compliance in Ampere."""
        self.singleComplianceSpinBox.setValue(value * 1000 * 1000)

    def continueInCompliance(self) -> bool:
        """Retruns True if continue in compliance is enabled."""
        return self.continueInComplianceCheckBox.isChecked()

    def setContinueInCompliance(self, enabled: bool) -> None:
        """Set True if continue in compliance."""
        self.continueInComplianceCheckBox.setChecked(enabled)

    def itDuration(self) -> float:
        """Returns It duration in seconds or zero for unlimited duration."""
        return self.itDurationSpinBox.value() * 60 * 60

    def setItDuration(self, value: float) -> None:
        """Set It duration in seconds or zero for unlimited duration."""
        self.itDurationSpinBox.setValue(value / 60 / 60)

    def itInterval(self) -> float:
        """Returns It measurement interval in seconds."""
        return self.itIntervalSpinBox.value()

    def setItInterval(self, value: float) -> None:
        """Set It measurement interval in seconds."""
        self.itIntervalSpinBox.setValue(value)

    def operator(self) -> str:
        """Returns current operator."""
        return self.operatorComboBox.currentText()

    def path(self) -> str:
        """Returns current absolute path."""
        return os.path.normpath(self.pathComboBox.currentText())

    def readSettings(self) -> None:
        settings = QtCore.QSettings()
        home = os.path.join(os.path.expanduser("~"), "longterm")
        names = settings.value("operators") or []
        index = settings.value("currentOperator", 0, type=int)
        path = settings.value("path", home)
        self.operatorComboBox.addItems(names)
        self.operatorComboBox.setCurrentIndex(min(index, len(names) - 1))
        self.operatorComboBox.currentIndexChanged[str].connect(self.onOperatorChanged)
        self.pathComboBox.addItem(path)
        self.pathComboBox.setCurrentText(path)
        if home != path:
            self.pathComboBox.addItem(home)
        self.setEnvironEnabled(settings.value("useEnviron", True, type=bool))
        self.setShuntBoxEnabled(settings.value("useShuntBox", True, type=bool))
        self.setIvEndVoltage(settings.value("ivEndVoltage", 800.0, type=float))
        self.onIvEndVoltageChanged()
        self.setIvStep(settings.value("ivStep", 5.0, type=float))
        self.setIvDelay(settings.value("ivDelay", 1.0, type=float))
        self.setBiasVoltage(settings.value("biasVoltage", 600.0, type=float))
        self.setTotalCompliance(
            settings.value("totalCompliance", 80.0 / 1000 / 1000, type=float)
        )
        self.setSingleCompliance(
            settings.value("singleCompliance", 25.0 / 1000 / 1000, type=float)
        )
        self.setContinueInCompliance(
            settings.value("continueInCompliance", True, type=bool)
        )
        self.setItDuration(settings.value("itDuration", 0.0, type=float))
        self.setItInterval(settings.value("itInterval", 60.0, type=float))
        self.smuWidget.setFilterEnable(
            settings.value("smu/filter/enable", False, type=bool)
        )
        self.smuWidget.setFilterType(
            settings.value("smu/filter/type", "repeat", type=str)
        )
        self.smuWidget.setFilterCount(settings.value("smu/filter/count", 10, type=int))
        self.dmmWidget.setFilterEnable(
            settings.value("dmm/filter/enable", False, type=bool)
        )
        self.dmmWidget.setFilterType(
            settings.value("dmm/filter/type", "repeat", type=str)
        )
        self.dmmWidget.setFilterCount(settings.value("dmm/filter/count", 10, type=int))
        self.dmmWidget.setChannelsSlot(settings.value("dmm/channels/slot", 1, type=int))
        self.dmmWidget.setChannelsOffset(settings.value("dmm/channels/offset", 0, type=int))
        self.dmmWidget.setTriggerDelayAuto(settings.value("dmm/trigger/delayAuto", True, type=bool))
        self.dmmWidget.setTriggerDelay(settings.value("dmm/trigger/delay", 0, type=float))

    def writeSettings(self):
        settings = QtCore.QSettings()
        settings.setValue("useEnviron", self.isEnvironEnabled())
        settings.setValue("useShuntBox", self.isShuntBoxEnabled())
        settings.setValue("ivEndVoltage", self.ivEndVoltage())
        settings.setValue("ivStep", self.ivStep())
        settings.setValue("ivDelay", self.ivDelay())
        settings.setValue("biasVoltage", self.biasVoltage())
        settings.setValue("totalCompliance", self.totalCompliance())
        settings.setValue("singleCompliance", self.singleCompliance())
        settings.setValue("continueInCompliance", self.continueInCompliance())
        settings.setValue("itDuration", self.itDuration())
        settings.setValue("itInterval", self.itInterval())
        settings.setValue("smu/filter/enable", self.smuWidget.filterEnable())
        settings.setValue("smu/filter/type", self.smuWidget.filterType())
        settings.setValue("smu/filter/count", self.smuWidget.filterCount())
        settings.setValue("dmm/filter/enable", self.dmmWidget.filterEnable())
        settings.setValue("dmm/filter/type", self.dmmWidget.filterType())
        settings.setValue("dmm/filter/count", self.dmmWidget.filterCount())
        settings.setValue("dmm/channels/slot", self.dmmWidget.channelsSlot())
        settings.setValue("dmm/channels/offset", self.dmmWidget.channelsOffset())
        settings.setValue("dmm/trigger/delayAuto", self.dmmWidget.triggerDelayAuto())
        settings.setValue("dmm/trigger/delay", self.dmmWidget.triggerDelay())

    @QtCore.pyqtSlot()
    def onStart(self):
        self.startPushButton.setChecked(True)
        self.startPushButton.setEnabled(False)
        self.stopPushButton.setChecked(False)
        self.stopPushButton.setEnabled(True)
        self.ctsCheckBox.setEnabled(False)
        self.shuntBoxCheckBox.setEnabled(False)
        self.ivEndVoltageSpinBox.setEnabled(False)
        self.ivStepSpinBox.setEnabled(False)
        self.biasVoltageSpinBox.setEnabled(False)
        self.smuWidget.filterEnableComboBox.setEnabled(False)
        self.smuWidget.filterTypeComboBox.setEnabled(False)
        self.smuWidget.filterCountSpinBox.setEnabled(False)
        self.dmmWidget.filterEnableComboBox.setEnabled(False)
        self.dmmWidget.filterTypeComboBox.setEnabled(False)
        self.dmmWidget.filterCountSpinBox.setEnabled(False)
        self.dmmWidget.slotComboBox.setEnabled(False)
        self.dmmWidget.offsetSpinBox.setEnabled(False)
        self.dmmWidget.triggerDelayAutoCheckBox.setEnabled(False)
        self.dmmWidget.triggerDelaySpinBox.setEnabled(False)
        self.operatorGroupBox.setEnabled(False)
        self.pathGroupBox.setEnabled(False)
        self.started.emit()

    @QtCore.pyqtSlot()
    def onStop(self):
        self.stopPushButton.setChecked(False)
        self.stopPushButton.setEnabled(False)
        self.stopRequest.emit()

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.startPushButton.setChecked(False)
        self.startPushButton.setEnabled(True)
        self.stopPushButton.setChecked(True)
        self.stopPushButton.setEnabled(False)
        self.ctsCheckBox.setEnabled(True)
        self.shuntBoxCheckBox.setEnabled(True)
        self.ivEndVoltageSpinBox.setEnabled(True)
        self.ivStepSpinBox.setEnabled(True)
        self.biasVoltageSpinBox.setEnabled(True)
        self.smuWidget.filterEnableComboBox.setEnabled(True)
        self.smuWidget.filterTypeComboBox.setEnabled(self.smuWidget.filterEnable())
        self.smuWidget.filterCountSpinBox.setEnabled(self.smuWidget.filterEnable())
        self.dmmWidget.filterEnableComboBox.setEnabled(True)
        self.dmmWidget.filterTypeComboBox.setEnabled(self.dmmWidget.filterEnable())
        self.dmmWidget.filterCountSpinBox.setEnabled(self.dmmWidget.filterEnable())
        self.dmmWidget.slotComboBox.setEnabled(True)
        self.dmmWidget.offsetSpinBox.setEnabled(True)
        self.dmmWidget.triggerDelayAutoCheckBox.setEnabled(True)
        self.dmmWidget.triggerDelaySpinBox.setEnabled(not self.dmmWidget.triggerDelayAuto())
        self.operatorGroupBox.setEnabled(True)
        self.pathGroupBox.setEnabled(True)
        self.halted.emit()

    @QtCore.pyqtSlot()
    def onSelectPath(self):
        """Select output directory using a file dialog."""
        path = self.pathComboBox.currentText() or QtCore.QDir.home().path()
        path = QtWidgets.QFileDialog.getExistingDirectory(
            self, self.tr("Select Output Directory"), path
        )
        if path:
            self.pathComboBox.addItem(path)
            self.pathComboBox.setCurrentText(path)
            settings = QtCore.QSettings()
            settings.setValue("path", path)

    @QtCore.pyqtSlot(str)
    def onOperatorChanged(self, name):
        """Store current operator name to settings."""
        settings = QtCore.QSettings()
        operators = settings.value("operators") or []
        if name not in operators:
            operators.append(name)
        settings.setValue("operators", operators)
        settings.setValue("currentOperator", operators.index(name))


class SMUWidget(QtWidgets.QWidget):

    filterEnableChanged = QtCore.pyqtSignal(bool)
    filterTypeChanged = QtCore.pyqtSignal(str)
    filterCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filterEnableLabel = QtWidgets.QLabel()
        self.filterEnableLabel.setText("Enable")

        self.filterEnableComboBox = QtWidgets.QComboBox()
        self.filterEnableComboBox.addItem("Off")
        self.filterEnableComboBox.addItem("On")

        self.filterTypeLabel = QtWidgets.QLabel()
        self.filterTypeLabel.setText("Type")

        self.filterTypeComboBox = QtWidgets.QComboBox()
        self.filterTypeComboBox.addItem("Repeat")
        self.filterTypeComboBox.addItem("Moving")

        self.filterCountLabel = QtWidgets.QLabel()
        self.filterCountLabel.setText("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setMinimum(0)
        self.filterCountSpinBox.setMaximum(100)
        self.filterCountSpinBox.setValue(10)

        self.filterGroupBox = QtWidgets.QGroupBox()
        self.filterGroupBox.setTitle("Filter")
        self.filterGroupBox.setMinimumWidth(140)

        filterGroupBoxLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterGroupBoxLayout.addWidget(self.filterEnableLabel)
        filterGroupBoxLayout.addWidget(self.filterEnableComboBox)
        filterGroupBoxLayout.addWidget(self.filterTypeLabel)
        filterGroupBoxLayout.addWidget(self.filterTypeComboBox)
        filterGroupBoxLayout.addWidget(self.filterCountLabel)
        filterGroupBoxLayout.addWidget(self.filterCountSpinBox)
        filterGroupBoxLayout.addStretch()

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self.filterGroupBox)
        layout.addStretch()
        layout.setStretch(0, 1)
        layout.setStretch(1, 2)

        self.filterEnableComboBox.currentIndexChanged.connect(
            self.onFilterEnableChanged
        )
        self.filterTypeComboBox.currentIndexChanged.connect(self.onFilterTypeChanged)
        self.filterCountSpinBox.editingFinished.connect(self.onFilterCountChanged)

        self.onFilterEnableChanged()
        self.onFilterTypeChanged()
        self.onFilterCountChanged()

    def filterEnable(self):
        """Returns filter enable state."""
        return bool(self.filterEnableComboBox.currentIndex())

    def setFilterEnable(self, enabled):
        """Set filter enable state."""
        self.filterEnableComboBox.setCurrentIndex(int(enabled))

    def filterType(self):
        """Returns filter type."""
        return self.filterTypeComboBox.currentText().lower()

    def setFilterType(self, type):
        """Set filter type."""
        index = self.filterTypeComboBox.findText(type.title())
        self.filterTypeComboBox.setCurrentIndex(max(0, index))

    def filterCount(self):
        """Returns filter count."""
        return self.filterCountSpinBox.value()

    def setFilterCount(self, count):
        """Set filter count."""
        self.filterCountSpinBox.setValue(count)

    @QtCore.pyqtSlot()
    def onFilterEnableChanged(self):
        enabled = self.filterEnable()
        self.filterTypeComboBox.setEnabled(enabled)
        self.filterCountSpinBox.setEnabled(enabled)
        self.filterEnableChanged.emit(enabled)

    @QtCore.pyqtSlot()
    def onFilterTypeChanged(self):
        self.filterTypeChanged.emit(self.filterType())

    @QtCore.pyqtSlot()
    def onFilterCountChanged(self):
        self.filterCountChanged.emit(self.filterCount())


class DMMWidget(QtWidgets.QWidget):

    filterEnableChanged = QtCore.pyqtSignal(bool)
    filterTypeChanged = QtCore.pyqtSignal(str)
    filterCountChanged = QtCore.pyqtSignal(int)
    channelsSlotChanged = QtCore.pyqtSignal(int)
    channelsOffsetChanged = QtCore.pyqtSignal(int)
    triggerDelayAutoChanged = QtCore.pyqtSignal(bool)
    triggerDelayChanged = QtCore.pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.filterEnableLabel = QtWidgets.QLabel()
        self.filterEnableLabel.setText("Enable")

        self.filterEnableComboBox = QtWidgets.QComboBox()
        self.filterEnableComboBox.addItem("Off")
        self.filterEnableComboBox.addItem("On")

        self.filterTypeLabel = QtWidgets.QLabel()
        self.filterTypeLabel.setText("Type")

        self.filterTypeComboBox = QtWidgets.QComboBox()
        self.filterTypeComboBox.addItem("Repeat")
        self.filterTypeComboBox.addItem("Moving")

        self.filterCountLabel = QtWidgets.QLabel()
        self.filterCountLabel.setText("Count")

        self.filterCountSpinBox = QtWidgets.QSpinBox()
        self.filterCountSpinBox.setMinimum(0)
        self.filterCountSpinBox.setMaximum(100)
        self.filterCountSpinBox.setValue(10)

        self.filterGroupBox = QtWidgets.QGroupBox(self)
        self.filterGroupBox.setTitle("Filter")
        # self.filterGroupBox.setMinimumWidth(140)

        filterGroupBoxLayout = QtWidgets.QVBoxLayout(self.filterGroupBox)
        filterGroupBoxLayout.addWidget(self.filterEnableLabel)
        filterGroupBoxLayout.addWidget(self.filterEnableComboBox)
        filterGroupBoxLayout.addWidget(self.filterTypeLabel)
        filterGroupBoxLayout.addWidget(self.filterTypeComboBox)
        filterGroupBoxLayout.addWidget(self.filterCountLabel)
        filterGroupBoxLayout.addWidget(self.filterCountSpinBox)
        filterGroupBoxLayout.addStretch()

        self.slotLabel = QtWidgets.QLabel(self)
        self.slotLabel.setText("Slot")

        self.slotComboBox = QtWidgets.QComboBox(self)
        self.slotComboBox.addItem("Slot 1", 1)
        self.slotComboBox.addItem("Slot 2", 2)

        self.offsetLabel = QtWidgets.QLabel(self)
        self.offsetLabel.setText("Offset")

        self.offsetSpinBox = QtWidgets.QSpinBox(self)
        self.offsetSpinBox.setRange(0, 32)

        self.channelsGroupBox = QtWidgets.QGroupBox(self)
        self.channelsGroupBox.setTitle("Channels")

        channelsGroupBoxLayout = QtWidgets.QVBoxLayout(self.channelsGroupBox)
        channelsGroupBoxLayout.addWidget(self.slotLabel)
        channelsGroupBoxLayout.addWidget(self.slotComboBox)
        channelsGroupBoxLayout.addWidget(self.offsetLabel)
        channelsGroupBoxLayout.addWidget(self.offsetSpinBox)

        self.triggerDelayAutoCheckBox = QtWidgets.QCheckBox(self)
        self.triggerDelayAutoCheckBox.setText("Auto Delay")

        self.triggerDelayLabel = QtWidgets.QLabel(self)
        self.triggerDelayLabel.setText("Delay")

        self.triggerDelaySpinBox = QtWidgets.QDoubleSpinBox(self)
        self.triggerDelaySpinBox.setRange(0, 9999)
        self.triggerDelaySpinBox.setDecimals(3)
        self.triggerDelaySpinBox.setSuffix(" s")

        self.triggerGroupBox = QtWidgets.QGroupBox(self)
        self.triggerGroupBox.setTitle("Trigger")

        triggerGroupBoxLayout = QtWidgets.QVBoxLayout(self.triggerGroupBox)
        triggerGroupBoxLayout.addWidget(self.triggerDelayAutoCheckBox)
        triggerGroupBoxLayout.addWidget(self.triggerDelayLabel)
        triggerGroupBoxLayout.addWidget(self.triggerDelaySpinBox)
        triggerGroupBoxLayout.addStretch()

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.filterGroupBox, 0, 0, 2, 1)
        layout.addWidget(self.channelsGroupBox, 0, 1)
        layout.addWidget(self.triggerGroupBox, 1, 1)
        layout.setColumnStretch(0, 1)
        layout.setColumnStretch(1, 1)
        layout.setColumnStretch(2, 1)

        self.filterEnableComboBox.currentIndexChanged.connect(
            self.onFilterEnableChanged
        )
        self.filterTypeComboBox.currentIndexChanged.connect(self.onFilterTypeChanged)
        self.filterCountSpinBox.editingFinished.connect(self.onFilterCountChanged)
        self.slotComboBox.currentIndexChanged.connect(self.onChannelsSlotChanged)
        self.offsetSpinBox.editingFinished.connect(self.onFilterCountChanged)
        self.triggerDelayAutoCheckBox.stateChanged.connect(self.onTriggerDelayAutoChanged)
        self.triggerDelaySpinBox.editingFinished.connect(self.onTriggerDelayChanged)

        self.onFilterEnableChanged()
        self.onFilterTypeChanged()
        self.onFilterCountChanged()
        self.onChannelsSlotChanged()
        self.onChannelsOffsetChanged()

    def filterEnable(self):
        """Returns filter enable state."""
        return bool(self.filterEnableComboBox.currentIndex())

    def setFilterEnable(self, enabled):
        """Set filter enable state."""
        self.filterEnableComboBox.setCurrentIndex(int(enabled))

    def filterType(self):
        """Returns filter type."""
        return self.filterTypeComboBox.currentText().lower()

    def setFilterType(self, type):
        """Set filter type."""
        index = self.filterTypeComboBox.findText(type.title())
        self.filterTypeComboBox.setCurrentIndex(max(0, index))

    def filterCount(self):
        """Returns filter count."""
        return self.filterCountSpinBox.value()

    def setFilterCount(self, count):
        """Set filter count."""
        self.filterCountSpinBox.setValue(count)

    def channelsSlot(self) -> int:
        return self.slotComboBox.currentData() or 0

    def setChannelsSlot(self, slot: int) -> None:
        index = self.slotComboBox.findData(slot)
        self.slotComboBox.setCurrentIndex(index)

    def channelsOffset(self) -> int:
        return self.offsetSpinBox.value()

    def setChannelsOffset(self, offset: int) -> None:
        self.offsetSpinBox.setValue(offset)

    def triggerDelayAuto(self) -> bool:
        return self.triggerDelayAutoCheckBox.isChecked()

    def setTriggerDelayAuto(self, enabled: bool) -> None:
        self.triggerDelayAutoCheckBox.setChecked(enabled)

    def triggerDelay(self) -> float:
        return self.triggerDelaySpinBox.value()

    def setTriggerDelay(self, delay: float) -> None:
        self.triggerDelaySpinBox.setValue(delay)

    @QtCore.pyqtSlot()
    def onFilterEnableChanged(self):
        enabled = self.filterEnable()
        self.filterTypeComboBox.setEnabled(enabled)
        self.filterCountSpinBox.setEnabled(enabled)
        self.filterEnableChanged.emit(enabled)

    @QtCore.pyqtSlot()
    def onFilterTypeChanged(self):
        self.filterTypeChanged.emit(self.filterType())

    @QtCore.pyqtSlot()
    def onFilterCountChanged(self):
        self.filterCountChanged.emit(self.filterCount())

    @QtCore.pyqtSlot()
    def onChannelsSlotChanged(self):
        self.channelsSlotChanged.emit(self.channelsSlot())

    @QtCore.pyqtSlot()
    def onChannelsOffsetChanged(self):
        self.channelsOffsetChanged.emit(self.channelsOffset())

    @QtCore.pyqtSlot()
    def onTriggerDelayAutoChanged(self):
        enabled = self.triggerDelayAuto()
        self.triggerDelayAutoChanged.emit(enabled)
        self.triggerDelaySpinBox.setEnabled(not enabled)

    @QtCore.pyqtSlot()
    def onTriggerDelayChanged(self):
        self.triggerDelayChanged.emit(self.triggerDelay())
