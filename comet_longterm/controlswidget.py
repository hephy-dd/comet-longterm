import os

from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

class ControlsWidget(QtWidgets.QWidget, UiLoaderMixin):

    started = QtCore.pyqtSignal()
    stopRequest = QtCore.pyqtSignal()
    calibrate = QtCore.pyqtSignal()

    ivEndVoltageChanged = QtCore.pyqtSignal(float)
    ivStepChanged = QtCore.pyqtSignal(float)
    ivIntervalChanged = QtCore.pyqtSignal(float)
    biasVoltageChanged = QtCore.pyqtSignal(float)
    totalComplianceChanged = QtCore.pyqtSignal(float)
    singleComplianceChanged = QtCore.pyqtSignal(float)
    continueInComplianceChanged = QtCore.pyqtSignal(bool)
    itDurationChanged = QtCore.pyqtSignal(float)
    itIntervalChanged = QtCore.pyqtSignal(float)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.loadSettings()

        # Setup signals
        self.ui.ivEndVoltageSpinBox.valueChanged.connect(lambda: self.ivEndVoltageChanged.emit(self.ivEndVoltage()))
        self.ui.ivStepSpinBox.valueChanged.connect(lambda: self.ivStepChanged.emit(self.ivStep()))
        self.ui.ivIntervalSpinBox.valueChanged.connect(lambda: self.ivIntervalChanged.emit(self.ivInterval()))
        self.ui.biasVoltageSpinBox.valueChanged.connect(lambda: self.biasVoltageChanged.emit(self.biasVoltage()))
        self.ui.totalComplianceSpinBox.valueChanged.connect(lambda: self.totalComplianceChanged.emit(self.totalCompliance()))
        self.ui.singleComplianceSpinBox.valueChanged.connect(lambda: self.singleComplianceChanged.emit(self.singleCompliance()))
        self.ui.continueInComplianceCheckBox.toggled.connect(lambda: self.continueInComplianceChanged.emit(self.continueInCompliance()))
        self.ui.itDurationSpinBox.valueChanged.connect(lambda: self.itDurationChanged.emit(self.itDuration()))
        self.ui.itIntervalSpinBox.valueChanged.connect(lambda: self.itIntervalChanged.emit(self.itInterval()))

    def ivEndVoltage(self):
        """Returns IV ramp up end voltage in volts."""
        return self.ui.ivEndVoltageSpinBox.value()

    def setIvEndVoltage(self, value):
        """Set IV ramp up end voltage in volts."""
        self.ui.ivEndVoltageSpinBox.setValue(value)

    def ivStep(self):
        """Returns IV ramp up step size in volts."""
        return self.ui.ivStepSpinBox.value()

    def setIvStep(self, value):
        """Set IV ramp up step size in volts."""
        self.ui.ivStepSpinBox.setValue(value)

    def ivInterval(self):
        """Returns IV measurement interval in seconds."""
        return self.ui.ivIntervalSpinBox.value()

    def setIvInterval(self, value):
        """Set IV measurement interval in seconds."""
        self.ui.ivIntervalSpinBox.setValue(value)

    def biasVoltage(self):
        """Returns It bias voltage in volts."""
        return self.ui.biasVoltageSpinBox.value()

    def setBiasVoltage(self, value):
        """Set It bias voltage in volts."""
        self.ui.biasVoltageSpinBox.setValue(value)

    def totalCompliance(self):
        """Returns total compliance in Ampere."""
        return self.ui.totalComplianceSpinBox.value() / 1000 / 1000

    def setTotalCompliance(self, value):
        """Set total compliance in Ampere."""
        self.ui.totalComplianceSpinBox.setValue(value * 1000 * 1000)

    def singleCompliance(self):
        """Returns single compliance in Ampere."""
        return self.ui.singleComplianceSpinBox.value() / 1000 / 1000

    def setSingleCompliance(self, value):
        """Set single compliance in Ampere."""
        self.ui.singleComplianceSpinBox.setValue(value * 1000 * 1000)

    def continueInCompliance(self):
        """Retruns True if continue in compliance is enabled."""
        return self.ui.continueInComplianceCheckBox.isChecked()

    def setContinueInCompliance(self, enabled):
        """Set True if continue in compliance."""
        self.ui.continueInComplianceCheckBox.setChecked(enabled)

    def itDuration(self):
        """Returns It duration in seconds or zero for unlimited duration."""
        return self.ui.itDurationSpinBox.value() * 60 * 60

    def setItDuration(self, value):
        """Set It duration in seconds or zero for unlimited duration."""
        self.ui.itDurationSpinBox.setValue(value / 60 / 60)

    def itInterval(self):
        """Returns It measurement interval in seconds."""
        return self.ui.itIntervalSpinBox.value()

    def setItInterval(self, value):
        """Set It measurement interval in seconds."""
        self.ui.itIntervalSpinBox.setValue(value)

    def operator(self):
        """Returns current operator."""
        return self.ui.operatorComboBox.currentText()

    def path(self):
        """Returns current absolute path."""
        return os.path.normpath(self.ui.pathComboBox.currentText())

    def loadSettings(self):
        settings = QtCore.QSettings()
        home = os.path.join(os.path.expanduser("~"), 'longterm')
        names = settings.value('operators', []) or [] # HACK
        index = settings.value('currentOperator', 0, type=int)
        path = settings.value('path', home)
        self.ui.operatorComboBox.addItems(names)
        self.ui.operatorComboBox.setCurrentIndex(min(index, len(names) - 1))
        self.ui.operatorComboBox.currentIndexChanged[str].connect(self.onOperatorChanged)
        self.ui.pathComboBox.addItem(path)
        self.ui.pathComboBox.setCurrentText(path)
        if home != path:
            self.ui.pathComboBox.addItem(home)
        self.setIvEndVoltage(settings.value('ivEndVoltage', 800.0, type=float))
        self.setIvStep(settings.value('ivStep', 5.0, type=float))
        self.setIvInterval(settings.value('ivInterval', 10.0, type=float))
        self.setBiasVoltage(settings.value('biasVoltage', 600.0, type=float))
        self.setTotalCompliance(settings.value('totalCompliance', 80.0 / 1000 / 1000, type=float))
        self.setSingleCompliance(settings.value('singleCompliance', 25.0 / 1000 / 1000, type=float))
        self.setContinueInCompliance(settings.value('continueInCompliance', False, type=bool))
        self.setItDuration(settings.value('itDuration', 0.0, type=float))
        self.setItInterval(settings.value('itInterval', 60.0, type=float))

    def storeSettings(self):
        settings = QtCore.QSettings()
        settings.setValue('ivEndVoltage', self.ivEndVoltage())
        settings.setValue('inStep', self.ivStep())
        settings.setValue('ivInterval', self.ivInterval())
        settings.setValue('biasVoltage', self.biasVoltage())
        settings.setValue('totalCompliance', self.totalCompliance())
        settings.setValue('singleCompliance', self.singleCompliance())
        settings.setValue('continueInCompliance', self.continueInCompliance())
        settings.setValue('itDuration', self.itDuration())
        settings.setValue('itInterval', self.itInterval())

    @QtCore.pyqtSlot()
    def onStart(self):
        self.ui.startPushButton.setChecked(True)
        self.ui.startPushButton.setEnabled(False)
        self.ui.stopPushButton.setChecked(False)
        self.ui.stopPushButton.setEnabled(True)
        self.ui.calibPushButton.setEnabled(False)
        self.ui.ivEndVoltageSpinBox.setEnabled(False)
        self.ui.ivStepSpinBox.setEnabled(False)
        self.ui.biasVoltageSpinBox.setEnabled(False)
        self.ui.operatorGroupBox.setEnabled(False)
        self.ui.pathGroupBox.setEnabled(False)
        self.started.emit()

    @QtCore.pyqtSlot()
    def onStop(self):
        self.ui.stopPushButton.setChecked(False)
        self.ui.stopPushButton.setEnabled(False)
        self.stopRequest.emit()

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.ui.startPushButton.setChecked(False)
        self.ui.startPushButton.setEnabled(True)
        self.ui.stopPushButton.setChecked(True)
        self.ui.stopPushButton.setEnabled(False)
        self.ui.calibPushButton.setEnabled(True)
        self.ui.ivEndVoltageSpinBox.setEnabled(True)
        self.ui.ivStepSpinBox.setEnabled(True)
        self.ui.biasVoltageSpinBox.setEnabled(True)
        self.ui.operatorGroupBox.setEnabled(True)
        self.ui.pathGroupBox.setEnabled(True)

    @QtCore.pyqtSlot()
    def onCalibrate(self):
        self.calibrate.emit()

    @QtCore.pyqtSlot()
    def onSelectPath(self):
        """Select output directory using a file dialog."""
        path = self.ui.pathComboBox.currentText() or QtCore.QDir.home().path()
        path = QtWidgets.QFileDialog.getExistingDirectory(self, self.tr("Select Output Directory"), path)
        if path:
            self.ui.pathComboBox.addItem(path)
            self.ui.pathComboBox.setCurrentText(path)
            settings = QtCore.QSettings()
            settings.setValue('path', path)

    @QtCore.pyqtSlot(str)
    def onOperatorChanged(self, name):
        """Store current operator name to settings."""
        settings = QtCore.QSettings()
        operators = settings.value('operators', []) or [] # HACK
        if name not in operators:
            operators.append(name)
        settings.setValue('operators', operators)
        settings.setValue('currentOperator', operators.index(name))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = ControlsWidget()
    w.show()
    app.exec_()
