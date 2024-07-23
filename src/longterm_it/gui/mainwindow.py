import logging
import os
import re
import traceback
import webbrowser
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

from .dashboard import DashboardWidget
from .logwindow import LogWindow
from .preferencesdialog import PreferencesDialog


class MainWindow(QtWidgets.QMainWindow):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)

        self.resources: dict = {}

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

        self.dashboard = DashboardWidget(self)
        self.setCentralWidget(self.dashboard)
        self.startAction.triggered.connect(self.dashboard.controlsWidget.startPushButton.click)
        self.stopAction.triggered.connect(self.dashboard.controlsWidget.stopPushButton.click)

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

    def readSettings(self) -> None:
        settings = QtCore.QSettings()
        settings.beginGroup("mainwindow")
        geometry = settings.value("geometry", QtCore.QByteArray(), QtCore.QByteArray)
        state = settings.value("state", QtCore.QByteArray(), QtCore.QByteArray)
        settings.endGroup()

        if not geometry.isEmpty():
            self.restoreGeometry(geometry)

        if not state.isEmpty():
            self.restoreState(state)

    def writeSettings(self) -> None:
        settings = QtCore.QSettings()
        settings.beginGroup("mainwindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("state", self.saveState())
        settings.endGroup()

    @QtCore.pyqtSlot(str)
    def showMessage(self, message: str) -> None:
        self.messageLabel.setText(message)
        self.messageLabel.show()

    @QtCore.pyqtSlot()
    def clearMessage(self) -> None:
        self.messageLabel.clear()
        self.messageLabel.hide()

    @QtCore.pyqtSlot(int, int)
    def showProgress(self, value: int, maximum: int) -> None:
        self.progressBar.setRange(0, maximum)
        self.progressBar.setValue(value)
        self.progressBar.show()

    @QtCore.pyqtSlot()
    def hideProgress(self) -> None:
        self.progressBar.hide()

    def onShowException(self, exc, tb=None) -> None:
        """Raise message box showing exception inforamtion."""
        logging.exception(exc)
        self.showMessage(self.tr("Exception occured."))
        self.hideProgress()
        details = "".join(traceback.format_tb(exc.__traceback__))
        dialog = QtWidgets.QMessageBox(self)
        dialog.setIcon(dialog.Icon.Critical)
        dialog.setWindowTitle(self.tr("Exception occured"))
        dialog.setText(format(format(exc), " <80"))  # quick-fix: increase width of dialog by appending spaces
        dialog.setDetailedText(details)
        dialog.exec()

    def onImportCalib(self) -> None:
        filename, filter_ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            self.tr("Open calibration resistors file..."),
            os.path.expanduser("~"),
        )
        if filename:
            # Yuck, quick'n dirty file parsing...
            try:
                resistors = []
                count = len(self.dashboard.sensors())
                with open(filename) as f:
                    for token in re.findall(r"\d+\s+", f.read()):
                        resistors.append(int(token))
                if len(resistors) < count:
                    raise RuntimeError(
                        "Missing calibration values, expected at least {}".format(count)
                    )
                for i in range(count):
                    logging.info("sensor[%s].resistivity = %s", i, resistors[i])
                    self.dashboard.sensors()[i].resistivity = resistors[i]
                QtWidgets.QMessageBox.information(
                    self,
                    self.tr("Success"),
                    self.tr("Sucessfully imported {} calibration resistor values.".format(count)),
                )
            except Exception as exc:
                self.onShowException(exc)

    def onShowLogWindow(self) -> None:
        self.logWindow.toBottom()
        self.logWindow.show()
        self.logWindow.raise_()

    def onShowPreferences(self) -> None:
        """Show modal preferences dialog."""
        context = {"resources": self.resources}
        dialog = PreferencesDialog(context, self)
        dialog.readSettings()
        if dialog.exec() == dialog.Accepted:
            dialog.writeSettings()
            QtWidgets.QMessageBox.information(
                self,
                self.tr("Preferences"),
                self.tr("Application restart required for changes to take effect."),
            )

    def onShowContents(self) -> None:
        """Open local webbrowser with contets URL."""
        contentsUrl = self.property("contentsUrl")
        if isinstance(contentsUrl, str):
            webbrowser.open(contentsUrl)

    def onShowAboutQt(self) -> None:
        """Show modal about Qt dialog."""
        QtWidgets.QMessageBox.aboutQt(self)

    def onShowAbout(self) -> None:
        """Show modal about dialog."""
        aboutText = self.property("aboutText")
        if isinstance(aboutText, str):
            QtWidgets.QMessageBox.about(self, "About", aboutText)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        dialog = QtWidgets.QMessageBox(self)
        dialog.setIcon(QtWidgets.QMessageBox.Question)
        dialog.setText(self.tr("Quit application?"))
        dialog.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        dialog.setDefaultButton(QtWidgets.QMessageBox.No)
        dialog.exec()

        if dialog.result() == dialog.Yes:
            progress = QtWidgets.QProgressDialog(self)
            progress.setRange(0, 0)
            progress.setValue(0)
            progress.setCancelButton(None)
            progress.setLabelText("Stopping active threads...")

            def stop_processes():
                self.meas_worker.abort()
                self.environ_worker.abort()
                if self.meas_thread.is_alive():
                    self.meas_thread.join()
                if self.environ_thread.is_alive():
                    self.environ_thread.join()
                progress.close()

            QtCore.QTimer.singleShot(250, stop_processes)
            progress.exec()
            self.logWindow.hide()
            self.logWindow.removeLogger(logging.getLogger())
            event.accept()
        else:
            event.ignore()
