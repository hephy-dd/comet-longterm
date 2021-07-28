import traceback

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

from .centralwidget import CentralWidget as Dashboard

class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Actions

        self.importCalibAction = QtWidgets.QAction(self.tr("Import &Calibrations..."))
        self.importCalibAction.setStatusTip("Import calibrations from file.")

        self.quitAction = QtWidgets.QAction("&Quit")
        self.quitAction.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.quitAction.setStatusTip("Quit the application")
        self.quitAction.triggered.connect(self.close)

        self.preferencesAction = QtWidgets.QAction(self.tr("Preferences..."))

        self.loggingAction = QtWidgets.QAction(self.tr("Logging..."))

        self.startAction = QtWidgets.QAction(self.tr("Start"))

        self.stopAction = QtWidgets.QAction(self.tr("Stop"))
        self.stopAction.setEnabled(False)

        self.contentsAction = QtWidgets.QAction("&Contents")
        self.contentsAction.setShortcut(QtGui.QKeySequence('F1'))

        self.aboutQtAction = QtWidgets.QAction("About &Qt")

        self.aboutAction = QtWidgets.QAction("&About")

        # Menus

        self.fileMenu = self.menuBar().addMenu(self.tr("&File"))
        self.fileMenu.addAction(self.importCalibAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.quitAction)

        self.editMenu = self.menuBar().addMenu(self.tr("&Edit"))
        self.editMenu.addAction(self.preferencesAction)

        self.viewMenu = self.menuBar().addMenu(self.tr("&View"))
        self.viewMenu.addAction(self.loggingAction)

        self.controlMenu = self.menuBar().addMenu(self.tr("&Control"))
        self.controlMenu.addAction(self.startAction)
        self.controlMenu.addAction(self.stopAction)

        self.helpMenu = self.menuBar().addMenu(self.tr("&Help"))
        self.helpMenu.addAction(self.contentsAction)
        self.helpMenu.addAction(self.aboutQtAction)
        self.helpMenu.addAction(self.aboutAction)

        # Central widget

        self.dashboard = Dashboard()
        self.setCentralWidget(self.dashboard)

        # Status bar

        self.messageLabel = QtWidgets.QLabel(self)
        self.messageLabel.hide()
        self.statusBar().addPermanentWidget(self.messageLabel)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

    @QtCore.pyqtSlot(str)
    def showMessage(self, message):
        self.messageLabel.setText(message)
        self.messageLabel.show()

    @QtCore.pyqtSlot()
    def clearMessage(self):
        self.messageLabel.clear()
        self.messageLabel.hide()

    @QtCore.pyqtSlot(int, int)
    def showProgress(self, value, maximum):
        self.progressBar.setRange(0, maximum)
        self.progressBar.setValue(value)
        self.progressBar.show()

    @QtCore.pyqtSlot()
    def hideProgress(self):
        self.progressBar.hide()

    @QtCore.pyqtSlot(object)
    def showException(self, exc):
        """Raise message box showing exception inforamtion."""
        details = ''.join(traceback.format_tb(exc.__traceback__))
        box = QtWidgets.QMessageBox(self)
        box.setIcon(box.Icon.Critical)
        box.setWindowTitle(self.tr("Error"))
        box.setText(format(exc))
        box.setDetailedText(details)
        box.exec()
        self.showMessage(self.tr("Error"))
        self.hideProgress()

class ProcessDialog(QtWidgets.QProgressDialog):

    def __init__(self, processes, parent=None):
        super().__init__(parent)
        self.processes = processes
        self.setRange(0, 0)
        self.setValue(0)
        self.setCancelButton(None)
        self.setLabelText("Stopping active threads...")

    @QtCore.pyqtSlot()
    def close(self):
        self.processes.stop()
        self.processes.join()
        super().close()

    def exec(self):
        QtCore.QTimer.singleShot(250, self.close)
        return super().exec()
