from PyQt5 import QtCore, QtGui, QtWidgets

from .dashboard import DashboardWidget


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        # Actions

        self.importCalibAction = QtWidgets.QAction(self)
        self.importCalibAction.setText(self.tr("Import &Calibrations..."))
        self.importCalibAction.setStatusTip("Import calibrations from file.")

        self.quitAction = QtWidgets.QAction(self)
        self.quitAction.setText("&Quit")
        self.quitAction.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.quitAction.setStatusTip("Quit the application")
        self.quitAction.triggered.connect(self.close)

        self.preferencesAction = QtWidgets.QAction(self)
        self.preferencesAction.setText(self.tr("Preferences..."))

        self.loggingAction = QtWidgets.QAction(self)
        self.loggingAction.setText(self.tr("Logging..."))

        self.startAction = QtWidgets.QAction(self)
        self.startAction.setText(self.tr("Start"))

        self.stopAction = QtWidgets.QAction(self)
        self.stopAction.setText(self.tr("Stop"))
        self.stopAction.setEnabled(False)

        self.contentsAction = QtWidgets.QAction(self)
        self.contentsAction.setText(self.tr("&Contents"))
        self.contentsAction.setShortcut(QtGui.QKeySequence("F1"))

        self.aboutQtAction = QtWidgets.QAction(self)
        self.aboutQtAction.setText(self.tr("About &Qt"))

        self.aboutAction = QtWidgets.QAction(self)
        self.aboutAction.setText(self.tr("&About"))

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

        self.setCentralWidget(DashboardWidget(self))

        # Status bar

        self.messageLabel = QtWidgets.QLabel(self)
        self.messageLabel.hide()
        self.statusBar().addPermanentWidget(self.messageLabel)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

    def loadSettings(self):
        settings = QtCore.QSettings()
        settings.beginGroup("mainwindow")
        geometry = settings.value("geometry", QtCore.QByteArray(), QtCore.QByteArray)
        state = settings.value("state", QtCore.QByteArray(), QtCore.QByteArray)
        settings.endGroup()

        if not geometry.isEmpty():
            self.restoreGeometry(geometry)

        if not state.isEmpty():
            self.restoreState(state)

    def storeSettings(self):
        settings = QtCore.QSettings()
        settings.beginGroup("mainwindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        settings.endGroup()

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
