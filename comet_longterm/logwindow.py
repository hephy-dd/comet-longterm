import logging
import threading
import html

from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5 import QtWidgets

__all__ = ['LogWindow', 'LogWidget']

class LogHandlerObject(QtCore.QObject):

    message =  QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

class LogHandler(logging.Handler):

    def __init__(self, parent=None):
        super().__init__()
        self.object = LogHandlerObject(parent)

    def emit(self, record):
        self.object.message.emit(record)

class LogWidget(QtWidgets.QTextEdit):

    MaximumEntries = 1024 * 1024

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.mutex = threading.RLock()
        self.handler = LogHandler(self)
        self.handler.object.message.connect(self.appendRecord)
        self.setLevel(logging.INFO)
        self.__entries = 0

    @property
    def entries(self):
        return self.__entries

    def setLevel(self, level):
        self.handler.setLevel(level)

    def addLogger(self, logger):
        logger.addHandler(self.handler)

    def removeLogger(self, logger):
        logger.removeHandler(self.handler)

    def toBottom(self):
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @QtCore.pyqtSlot(object)
    def appendRecord(self, record):
        with self.mutex:
            # Clear when exceeding maximum allowed entries...
            if self.entries > self.MaximumEntries:
                self.clear() # TODO
            # Get current scrollbar position
            scrollbar = self.verticalScrollBar()
            current_pos = scrollbar.value()
            # Lock to current position or to bottom
            lock_bottom = False
            if current_pos + 1 >= scrollbar.maximum():
                lock_bottom = True
            # Append foramtted log message
            self.append(self.formatRecord(record))
            self.__entries += 1
            # Scroll to bottom
            if lock_bottom:
                self.toBottom()
            else:
                scrollbar.setValue(current_pos)

    def clear(self):
        super().clear()
        self.__entries = 0

    @classmethod
    def formatTime(cls, seconds):
        dt = QtCore.QDateTime.fromMSecsSinceEpoch(seconds * 1000)
        return dt.toString("yyyy-MM-dd hh:mm:ss")

    @classmethod
    def formatRecord(cls, record):
        if record.levelno >= logging.ERROR:
            color = 'red'
        elif record.levelno >= logging.WARNING:
            color = 'orange'
        else:
            color = 'inherit'
        style = f"white-space:pre;color:{color};margin:0"
        timestamp = cls.formatTime(record.created)
        message = "{}\t{}\t{}".format(timestamp, record.levelname, record.getMessage())
        # Escape to HTML
        message = html.escape(message)
        return f"<span style=\"{style}\">{message}</span>"

class LogWindow(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(self.tr("Logging"))
        self.logHeader = QtWidgets.QLabel()
        self.logHeader.setTextFormat(QtCore.Qt.RichText)
        self.logHeader.setText("<span style=\"white-space:pre\">Time\t\tLevel\tMessage</span>")
        self.logWidget = LogWidget()
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(self.buttonBox.Close)
        self.buttonBox.rejected.connect(lambda: self.hide())
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.logHeader)
        layout.addWidget(self.logWidget)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)

    def setLevel(self, level):
        self.logWidget.setLevel(level)

    def addLogger(self, logger):
        self.logWidget.addLogger(logger)

    def removeLogger(self, logger):
        self.logWidget.removeLogger(logger)

    def toBottom(self):
        self.logWidget.toBottom()

    @QtCore.pyqtSlot()
    def clear(self):
        self.logWidget.clear()

    @QtCore.pyqtSlot(object)
    def appendRecord(self, record):
        self.logWidget.appendRecord(record)
