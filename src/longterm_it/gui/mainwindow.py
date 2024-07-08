import logging
import os
import re
import traceback
import webbrowser

from PyQt5 import QtCore, QtGui, QtWidgets

from .dashboard import DashboardWidget
from .logwindow import LogWindow
from .preferencesdialog import PreferencesDialog


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.resources = {}

        # Actions

        self.importCalibAction = QtWidgets.QAction(self)
        self.importCalibAction.setText(self.tr("Import &Calibrations..."))
        self.importCalibAction.setStatusTip("Import calibrations from file.")
        self.importCalibAction.triggered.connect(self.onImportCalib)

        self.quitAction = QtWidgets.QAction(self)
        self.quitAction.setText("&Quit")
        self.quitAction.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.quitAction.setStatusTip("Quit the application")
        self.quitAction.triggered.connect(self.close)

        self.preferencesAction = QtWidgets.QAction(self)
        self.preferencesAction.setText(self.tr("Preferences..."))
        self.preferencesAction.triggered.connect(self.onShowPreferences)

        self.loggingAction = QtWidgets.QAction(self)
        self.loggingAction.setText(self.tr("Logging..."))
        self.loggingAction.triggered.connect(self.onShowLogWindow)

        self.startAction = QtWidgets.QAction(self)
        self.startAction.setText(self.tr("Start"))

        self.stopAction = QtWidgets.QAction(self)
        self.stopAction.setText(self.tr("Stop"))
        self.stopAction.setEnabled(False)

        self.contentsAction = QtWidgets.QAction(self)
        self.contentsAction.setText(self.tr("&Contents"))
        self.contentsAction.setShortcut(QtGui.QKeySequence("F1"))
        self.contentsAction.triggered.connect(self.onShowContents)

        self.aboutQtAction = QtWidgets.QAction(self)
        self.aboutQtAction.setText(self.tr("About &Qt"))
        self.aboutQtAction.triggered.connect(self.onShowAboutQt)

        self.aboutAction = QtWidgets.QAction(self)
        self.aboutAction.setText(self.tr("&About"))
        self.aboutAction.triggered.connect(self.onShowAbout)

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
        self.helpMenu.addSeparator()
        self.helpMenu.addAction(self.aboutQtAction)
        self.helpMenu.addAction(self.aboutAction)

        # Central widget

        dashboard = DashboardWidget(self)
        self.setCentralWidget(dashboard)
        self.startAction.triggered.connect(dashboard.controlsWidget.startPushButton.click)
        self.stopAction.triggered.connect(dashboard.controlsWidget.stopPushButton.click)

        # Status bar

        self.messageLabel = QtWidgets.QLabel(self)
        self.messageLabel.hide()
        self.statusBar().addPermanentWidget(self.messageLabel)

        self.progressBar = QtWidgets.QProgressBar(self)
        self.progressBar.hide()
        self.statusBar().addPermanentWidget(self.progressBar)

        # Log Window
        self.logWindow = LogWindow()
        self.logWindow.resize(640, 420)
        self.logWindow.hide()

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
    def showProgress(self, value: int, maximum: int) -> None:
        self.progressBar.setRange(0, maximum)
        self.progressBar.setValue(value)
        self.progressBar.show()

    @QtCore.pyqtSlot()
    def hideProgress(self):
        self.progressBar.hide()

    def onShowException(self, exc, tb=None):
        """Raise message box showing exception inforamtion."""
        logging.exception(exc)
        self.showMessage(self.tr("Exception occured."))
        self.hideProgress()
        details = "".join(traceback.format_tb(exc.__traceback__))
        dialog = QtWidgets.QMessageBox(self)
        dialog.setIcon(dialog.Icon.Critical)
        dialog.setWindowTitle(self.tr("Exception occured"))
        dialog.setText(format(exc))
        dialog.setDetailedText(details)
        dialog.exec()

    def onImportCalib(self):
        widget = self.centralWidget()
        filename, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open calibration resistors file..."),
            os.path.expanduser("~"),
        )
        if filename:
            # Yuck, quick'n dirty file parsing...
            try:
                resistors = []
                count = len(widget.sensors())
                with open(filename) as f:
                    for token in re.findall(r"\d+\s+", f.read()):
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError(
                        "Missing calibration values, expected at least {}".format(count)
                    )
                for i in range(count):
                    logging.info("sensor[%s].resistivity = %s", i, resistors[i])
                    widget.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("Sucessfully imported {} calibration resistor values.".format(count)),
                )
            except Exception as exc:
                self.onShowException(exc)

    def onShowLogWindow(self):
        self.logWindow.toBottom()
        self.logWindow.show()
        self.logWindow.raise_()

    def onShowPreferences(self):
        """Show modal preferences dialog."""
        dialog = PreferencesDialog(self.resources, self)
        dialog.exec()

    def onShowContents(self):
        """Open local webbrowser with contets URL."""
        webbrowser.open(self.property("contentsUrl"))

    def onShowAboutQt(self):
        """Show modal about Qt dialog."""
        QtWidgets.QMessageBox.aboutQt(self)

    def onShowAbout(self):
        """Show modal about dialog."""
        QtWidgets.QMessageBox.about(self, "About", self.property("aboutText"))

    def closeEvent(self, event):
        dialog = QtWidgets.QMessageBox(self)
        dialog.setIcon(QtWidgets.QMessageBox.Question)
        dialog.setText(self.tr("Quit application?"))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setDefaultButton(QtWidgets.QMessageBox.No)
        dialog.exec()

        if dialog.result() == dialog.Yes:
            dialog = QtWidgets.QProgressDialog(self)
            dialog.setRange(0, 0)
            dialog.setValue(0)
            dialog.setCancelButton(None)
            dialog.setLabelText("Stopping active threads...")

            def stop_processes():
                self.meas_worker.abort()
                self.environ_worker.abort()
                if self.meas_thread.is_alive():
                    self.meas_thread.join()
                if self.environ_thread.is_alive():
                    self.environ_thread.join()
                dialog.close()

            QtCore.QTimer.singleShot(250, stop_processes)
            dialog.exec()
            self.logWindow.hide()
            self.logWindow.removeLogger(logging.getLogger())
            event.accept()
        else:
            event.ignore()
