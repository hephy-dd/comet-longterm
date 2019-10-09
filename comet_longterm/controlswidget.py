import os
import datetime

from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin
from .calibrationdialog import CalibrationDialog

class ControlsWidget(QtWidgets.QWidget, UiLoaderMixin):

    started = QtCore.pyqtSignal()
    stopRequest = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        settings = QtCore.QSettings()
        home = os.path.join(QtCore.QDir().homePath(), 'longterm')
        names = settings.value('operators', [])
        index = settings.value('currentOperator', 0, type=int)
        path = settings.value('path', home)
        self.ui.operatorComboBox.addItems(names)
        self.ui.operatorComboBox.setCurrentIndex(min(index, len(names) - 1))
        self.ui.operatorComboBox.currentIndexChanged[str].connect(self.onOperatorChanged)
        self.ui.pathComboBox.addItem(path)
        self.ui.pathComboBox.setCurrentText(path)
        if home != path:
            self.ui.pathComboBox.addItem(home)

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
        """Show calibration dialog."""
        dialog = CalibrationDialog(self)
        dialog.exec_()
        for i in range(len(self.parent().ui.sensorsWidget.sensors)):
            self.parent().ui.sensorsWidget.sensors[i].resistivity = dialog.resistivities[i]

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
        operators = settings.value('operators', [])
        if name not in operators:
            operators.append(name)
        settings.setValue('operators', operators)
        settings.setValue('currentOperator', operators.index(name))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = ControlsWidget()
    w.show()
    app.exec_()
