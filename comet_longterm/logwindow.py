import logging
import threading

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

__all__ = ['LogWindow', 'LogWidget']

class LogHandler(QtCore.QObject, logging.Handler):

    message = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

    def emit(self, record):
        self.message.emit(record)

class LogItem(QtWidgets.QTreeWidgetItem):

    TimeColumn = 0
    LevelColumn = 1
    MessageColumn = 2

    Colors = {
        logging.DEBUG: "grey",
        logging.INFO: "black",
        logging.WARNING: "orange",
        logging.ERROR: "red"
    }

    def __init__(self, record):
        super().__init__()
        self.setFromRecord(record)

    def setFromRecord(self, record):
        self.setText(self.TimeColumn, self.formatTime(record.created))
        self.setText(self.LevelColumn, record.levelname)
        self.setText(self.MessageColumn, record.getMessage())
        brush = QtGui.QBrush(QtGui.QColor(self.Colors.get(record.levelno)))
        self.setForeground(self.TimeColumn, brush)
        self.setForeground(self.LevelColumn, brush)
        self.setForeground(self.MessageColumn, brush)

    @classmethod
    def formatTime(cls, seconds):
        dt = QtCore.QDateTime.fromMSecsSinceEpoch(seconds * 1000)
        return dt.toString("yyyy-MM-dd hh:mm:ss")

class LogWidget(QtWidgets.QTreeWidget):

    HistorySize = 8192

    def __init__(self, parent=None):
        super().__init__(parent)
        self.mutex = threading.RLock()
        self.handler = LogHandler(self)
        self.handler.message.connect(self.appendRecord)
        self.setLevel(logging.INFO)
        self.setIndentation(0)
        self.headerItem().setText(0, self.tr("Time"))
        self.headerItem().setText(1, self.tr("Level"))
        self.headerItem().setText(2, self.tr("Message"))
        self.setColumnWidth(0, 128)
        self.setColumnWidth(1, 64)

    def setLevel(self, level):
        self.handler.setLevel(level)

    def addLogger(self, logger):
        logger.addHandler(self.handler)

    def removeLogger(self, logger):
        logger.removeHandler(self.handler)

    @QtCore.pyqtSlot(object)
    def appendRecord(self, record):
        item = LogItem(record)
        with self.mutex:
            self.addTopLevelItem(item)
            # Remove first records if exceeding history size.
            if self.HistorySize is not None:
                if self.topLevelItemCount() > self.HistorySize:
                    self.takeTopLevelItem(0)
            self.scrollToItem(item)

class LogWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Logging"))
        self.logWidget = LogWidget()
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.logWidget)
        self.setLayout(layout)

    def setLevel(self, level):
        self.logWidget.setLevel(level)

    def addLogger(self, logger):
        self.logWidget.addLogger(logger)

    def removeLogger(self, logger):
        self.logWidget.removeLogger(logger)

    @QtCore.pyqtSlot()
    def clear(self):
        self.logWidget.clear()

    @QtCore.pyqtSlot(object)
    def appendRecord(self, record):
        self.logWidget.appendRecord(record)
