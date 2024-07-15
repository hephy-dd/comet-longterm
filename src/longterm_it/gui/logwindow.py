import logging
import threading
import html
from datetime import datetime
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

__all__ = ["LogWindow", "LogWidget"]


class LogHandlerObject(QtCore.QObject):

    message = QtCore.pyqtSignal(logging.LogRecord)

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__(parent)


class LogHandler(logging.Handler):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None):
        super().__init__()
        self.object = LogHandlerObject(parent)

    def emit(self, record: logging.LogRecord) -> None:
        self.object.message.emit(record)


class LogWidget(QtWidgets.QTextEdit):

    MaximumEntries: int = 1024 * 1024

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QtGui.QFontDatabase.systemFont(QtGui.QFontDatabase.FixedFont))
        self.mutex = threading.RLock()
        self.handler = LogHandler(self)
        self.handler.object.message.connect(self.appendRecord)
        self.setLevel(logging.INFO)
        self.__entries: int = 0

    @property
    def entries(self) -> int:
        return self.__entries

    def setLevel(self, level) -> None:
        self.handler.setLevel(level)

    def addLogger(self, logger: logging.Logger) -> None:
        logger.addHandler(self.handler)

    def removeLogger(self, logger: logging.Logger) -> None:
        logger.removeHandler(self.handler)

    def toBottom(self) -> None:
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    @QtCore.pyqtSlot(logging.LogRecord)
    def appendRecord(self, record: logging.LogRecord) -> None:
        with self.mutex:
            # Clear when exceeding maximum allowed entries...
            if self.entries > self.MaximumEntries:
                self.clear()  # TODO
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

    def clear(self) -> None:
        super().clear()
        self.__entries = 0

    @classmethod
    def formatTime(cls, seconds: float) -> str:
        dt = datetime.fromtimestamp(seconds)
        return dt.strftime("%Y-%m-%d %H:%M:%S")

    @classmethod
    def formatRecord(cls, record: logging.LogRecord) -> str:
        if record.levelno >= logging.ERROR:
            color = "red"
        elif record.levelno >= logging.WARNING:
            color = "orange"
        else:
            color = "inherit"
        style = f"white-space:pre;color:{color};margin:0"
        timestamp = cls.formatTime(record.created)
        message = "{}\t{}\t{}".format(timestamp, record.levelname, record.getMessage())
        # Escape to HTML
        message = html.escape(message)
        return f'<span style="{style}">{message}</span>'


class LogWindow(QtWidgets.QWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Logging"))

        self.logHeader = QtWidgets.QLabel()
        self.logHeader.setTextFormat(QtCore.Qt.RichText)
        self.logHeader.setText(
            '<span style="white-space:pre">Time\t\tLevel\tMessage</span>'
        )

        self.logWidget = LogWidget()
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(self.buttonBox.Close)
        self.buttonBox.rejected.connect(lambda: self.hide())

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.logHeader)
        layout.addWidget(self.logWidget)
        layout.addWidget(self.buttonBox)

    def setLevel(self, level) -> None:
        self.logWidget.setLevel(level)

    def addLogger(self, logger: logging.Logger) -> None:
        self.logWidget.addLogger(logger)

    def removeLogger(self, logger: logging.Logger) -> None:
        self.logWidget.removeLogger(logger)

    def toBottom(self) -> None:
        self.logWidget.toBottom()

    @QtCore.pyqtSlot()
    def clear(self) -> None:
        self.logWidget.clear()

    @QtCore.pyqtSlot(logging.LogRecord)
    def appendRecord(self, record: logging.LogRecord) -> None:
        self.logWidget.appendRecord(record)
