import logging
import os

from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

logger = logging.getLogger(__name__)

class ControlsWidget(QtWidgets.QWidget, UiLoaderMixin):

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
    filterEnableChanged = QtCore.pyqtSignal(bool)
    filterTypeChanged = QtCore.pyqtSignal(str)
    filterCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.ui.operatorComboBox.setDuplicatesEnabled(False)

        self.loadSettings()

        # Setup signals
        self.ui.shuntBoxCheckBox.toggled.connect(lambda: self.useShuntBoxChanged.emit(self.isShuntBoxEnabled()))
        self.ui.ivEndVoltageSpinBox.editingFinished.connect(lambda: self.ivEndVoltageChanged.emit(self.ivEndVoltage()))
        self.ui.ivEndVoltageSpinBox.editingFinished.connect(self.onIvEndVoltageChanged)
        self.ui.ivStepSpinBox.editingFinished.connect(lambda: self.ivStepChanged.emit(self.ivStep()))
        self.ui.ivDelaySpinBox.editingFinished.connect(lambda: self.ivDelayChanged.emit(self.ivDelay()))
        self.ui.biasVoltageSpinBox.editingFinished.connect(lambda: self.biasVoltageChanged.emit(self.biasVoltage()))
        self.ui.totalComplianceSpinBox.editingFinished.connect(lambda: self.totalComplianceChanged.emit(self.totalCompliance()))
        self.ui.totalComplianceSpinBox.editingFinished.connect(self.onTotalComplianceChanged)
        self.ui.singleComplianceSpinBox.editingFinished.connect(lambda: self.singleComplianceChanged.emit(self.singleCompliance()))
        self.ui.continueInComplianceCheckBox.toggled.connect(lambda: self.continueInComplianceChanged.emit(self.continueInCompliance()))
        self.ui.itDurationSpinBox.editingFinished.connect(lambda: self.itDurationChanged.emit(self.itDuration()))
        self.ui.itIntervalSpinBox.editingFinished.connect(lambda: self.itIntervalChanged.emit(self.itInterval()))
        self.ui.multiFilterEnableComboBox.currentIndexChanged.connect(self.onFilterEnableChanged)
        self.ui.multiFilterTypeComboBox.currentIndexChanged.connect(lambda: self.filterTypeChanged.emit(self.filterType()))
        self.ui.multiFilterCountSpinBox.editingFinished.connect(lambda: self.filterCountChanged.emit(self.filterCount()))
        # Syncronize limits
        self.onIvEndVoltageChanged()
        self.onTotalComplianceChanged()
        self.onFilterEnableChanged()

    def onIvEndVoltageChanged(self):
        """Syncronize bias voltage and step with end voltage limit."""
        bias = self.ui.biasVoltageSpinBox.value()
        if self.ivEndVoltage() < 0:
            self.ui.biasVoltageSpinBox.setMinimum(self.ivEndVoltage())
            self.ui.biasVoltageSpinBox.setMaximum(0)
            self.ui.biasVoltageSpinBox.setValue(-abs(bias))
        else:
            self.ui.biasVoltageSpinBox.setMinimum(0)
            self.ui.biasVoltageSpinBox.setMaximum(self.ivEndVoltage())
            self.ui.biasVoltageSpinBox.setValue(abs(bias))
        self.ui.ivStepSpinBox.setMaximum(abs(self.ivEndVoltage()))

    def onTotalComplianceChanged(self):
        """Syncronize total/single compliance limit."""
        self.ui.singleComplianceSpinBox.setMaximum(self.totalCompliance() * 1000 * 1000) # in uA

    def isEnvironEnabled(self):
        """Returns True if use CTS is checked."""
        return self.ui.ctsCheckBox.isChecked()

    def setEnvironEnabled(self, value):
        """Set use CTS enabled."""
        self.ui.ctsCheckBox.setChecked(value)

    def isShuntBoxEnabled(self):
        """Returns True if use shunt box is checked."""
        return self.ui.shuntBoxCheckBox.isChecked()

    def setShuntBoxEnabled(self, value):
        """Set shunt box enabled."""
        self.ui.shuntBoxCheckBox.setChecked(value)

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

    def ivDelay(self):
        """Returns IV measurement interval in seconds."""
        return self.ui.ivDelaySpinBox.value() / 1000.

    def setIvDelay(self, value):
        """Set IV measurement interval in seconds."""
        self.ui.ivDelaySpinBox.setValue(value * 1000.)

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

    def filterEnable(self):
        """Returns filter enable state."""
        return bool(self.ui.multiFilterEnableComboBox.currentIndex())

    def setFilterEnable(self, enabled):
        """Set filter enable state."""
        self.ui.multiFilterEnableComboBox.setCurrentIndex(int(enabled))

    def filterType(self):
        """Returns filter type."""
        return self.ui.multiFilterTypeComboBox.currentText().lower()

    def setFilterType(self, type):
        """Set filter type."""
        index = self.ui.multiFilterTypeComboBox.findText(type.title())
        if index < 0:
            index = 0
        self.ui.multiFilterTypeComboBox.setCurrentIndex(index)

    def filterCount(self):
        """Returns filter count."""
        return self.ui.multiFilterCountSpinBox.value()

    def setFilterCount(self, count):
        """Set filter count."""
        self.ui.multiFilterCountSpinBox.setValue(count)

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
        self.setEnvironEnabled(settings.value('useEnviron', True, type=bool))
        self.setShuntBoxEnabled(settings.value('useShuntBox', True, type=bool))
        self.setIvEndVoltage(settings.value('ivEndVoltage', 800.0, type=float))
        self.setIvStep(settings.value('ivStep', 5.0, type=float))
        self.setIvDelay(settings.value('ivDelay', 1.0, type=float))
        self.setBiasVoltage(settings.value('biasVoltage', 600.0, type=float))
        self.setTotalCompliance(settings.value('totalCompliance', 80.0 / 1000 / 1000, type=float))
        self.setSingleCompliance(settings.value('singleCompliance', 25.0 / 1000 / 1000, type=float))
        self.setContinueInCompliance(settings.value('continueInCompliance', True, type=bool))
        self.setItDuration(settings.value('itDuration', 0.0, type=float))
        self.setItInterval(settings.value('itInterval', 60.0, type=float))
        self.setFilterEnable(settings.value('filterEnable', False, type=bool))
        self.setFilterType(settings.value('filterType', 'repeat', type=str))
        self.setFilterCount(settings.value('filterCount', 10, type=int))

    def storeSettings(self):
        settings = QtCore.QSettings()
        settings.setValue('useEnviron', self.isEnvironEnabled())
        settings.setValue('useShuntBox', self.isShuntBoxEnabled())
        settings.setValue('ivEndVoltage', self.ivEndVoltage())
        settings.setValue('ivStep', self.ivStep())
        settings.setValue('ivDelay', self.ivDelay())
        settings.setValue('biasVoltage', self.biasVoltage())
        settings.setValue('totalCompliance', self.totalCompliance())
        settings.setValue('singleCompliance', self.singleCompliance())
        settings.setValue('continueInCompliance', self.continueInCompliance())
        settings.setValue('itDuration', self.itDuration())
        settings.setValue('itInterval', self.itInterval())
        settings.setValue('filterEnable', self.filterEnable())
        settings.setValue('filterType', self.filterType())
        settings.setValue('filterCount', self.filterCount())

    @QtCore.pyqtSlot()
    def onFilterEnableChanged(self):
        enabled = self.filterEnable()
        self.ui.multiFilterTypeComboBox.setEnabled(enabled)
        self.ui.multiFilterCountSpinBox.setEnabled(enabled)
        self.filterEnableChanged.emit(enabled)

    @QtCore.pyqtSlot()
    def onStart(self):
        self.ui.startPushButton.setChecked(True)
        self.ui.startPushButton.setEnabled(False)
        self.ui.stopPushButton.setChecked(False)
        self.ui.stopPushButton.setEnabled(True)
        self.ui.ctsCheckBox.setEnabled(False)
        self.ui.shuntBoxCheckBox.setEnabled(False)
        self.ui.ivEndVoltageSpinBox.setEnabled(False)
        self.ui.ivStepSpinBox.setEnabled(False)
        self.ui.biasVoltageSpinBox.setEnabled(False)
        self.ui.multiFilterEnableComboBox.setEnabled(False)
        self.ui.multiFilterTypeComboBox.setEnabled(False)
        self.ui.multiFilterCountSpinBox.setEnabled(False)
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
        self.ui.ctsCheckBox.setEnabled(True)
        self.ui.shuntBoxCheckBox.setEnabled(True)
        self.ui.ivEndVoltageSpinBox.setEnabled(True)
        self.ui.ivStepSpinBox.setEnabled(True)
        self.ui.biasVoltageSpinBox.setEnabled(True)
        self.ui.multiFilterEnableComboBox.setEnabled(True)
        self.ui.multiFilterTypeComboBox.setEnabled(True)
        self.ui.multiFilterCountSpinBox.setEnabled(True)
        self.ui.operatorGroupBox.setEnabled(True)
        self.ui.pathGroupBox.setEnabled(True)
        self.halted.emit()

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
