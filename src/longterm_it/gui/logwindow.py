import logging
import threading
import html
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from PyQt5 import QtCore, QtGui, QtWidgets

__all__ = ["LogWindow"]


def setRowColor(item: QtWidgets.QTreeWidgetItem, color: QtGui.QBrush) -> None:
    """Set row color for QTreeWidgetItem."""
    for index in range(item.columnCount()):
        item.setForeground(index, color)


@dataclass
class Message:
    created: str
    level: str
    levelno: int
    message: str


class MessageQueue:
    def __init__(self, size: int) -> None:
        self._size = size
        self._lock = threading.RLock()
        self._messages: list[Message] = []

    def put(self, message: Message) -> None:
        with self._lock:
            self._messages.append(message)
            while len(self._messages) > self._size:
                self._messages.pop(0)

    def fetch(self) -> list[Message]:
        with self._lock:
            messages = self._messages[-self._size:]
            self._messages.clear()
            return messages


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


class LogWindow(QtWidgets.QWidget):

    MaximumMessageCount: int = 1000
    UpdateInterval: int = 250

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Logging"))

        self.messageQueue: MessageQueue = MessageQueue(self.MaximumMessageCount)

        self.handler = LogHandler(self)
        self.handler.object.message.connect(self.appendRecord)

        self.treeWidget = QtWidgets.QTreeWidget(self)
        self.treeWidget.setHeaderLabels(["Time", "Level", "Message"])
        self.treeWidget.setAlternatingRowColors(True)
        self.treeWidget.setRootIsDecorated(False)
        self.treeWidget.setSortingEnabled(False)
        self.treeWidget.setWordWrap(True)
        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeWidget.customContextMenuRequested.connect(self.showContextMenu)

        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setStandardButtons(self.buttonBox.Close)
        self.buttonBox.rejected.connect(lambda: self.hide())

        layout = QtWidgets.QGridLayout(self)
        layout.addWidget(self.treeWidget)
        layout.addWidget(self.buttonBox)

        self.updateTimer = QtCore.QTimer(self)
        self.updateTimer.timeout.connect(self.updateMessages)
        self.updateTimer.setInterval(self.UpdateInterval)
        self.updateTimer.start()

    def setLevel(self, level) -> None:
        self.handler.setLevel(level)

    def addLogger(self, logger: logging.Logger) -> None:
        logger.addHandler(self.handler)

    def removeLogger(self, logger: logging.Logger) -> None:
        logger.removeHandler(self.handler)

    def toBottom(self) -> None:
        item = self.treeWidget.topLevelItem(self.treeWidget.topLevelItemCount() - 1)
        if item:
            self.treeWidget.scrollToItem(item)

    @QtCore.pyqtSlot()
    def clear(self) -> None:
        self.treeWidget.clear()

    @QtCore.pyqtSlot()
    def updateMessages(self) -> None:
        with QtCore.QSignalBlocker(self.treeWidget):
            orange = QtGui.QBrush(QtGui.QColor("orange"))
            red = QtGui.QBrush(QtGui.QColor("red"))
            for message in self.messageQueue.fetch():
                item = QtWidgets.QTreeWidgetItem([message.created, message.level, message.message])
                color = None
                if message.levelno >= logging.WARNING:
                    color = orange
                if message.levelno >= logging.ERROR:
                    color = red
                if color:
                    setRowColor(item, color)
                self.treeWidget.addTopLevelItem(item)
                if self.treeWidget.topLevelItemCount() == 1:
                    for index in range(3):
                        self.treeWidget.resizeColumnToContents(index)
                self.truncateMessages()

    def truncateMessages(self) -> None:
        while self.treeWidget.topLevelItemCount() > self.MaximumMessageCount:
            item = self.treeWidget.takeTopLevelItem(0)
            del item

    @QtCore.pyqtSlot(logging.LogRecord)
    def appendRecord(self, record: logging.LogRecord) -> None:
        created = datetime.fromtimestamp(record.created).strftime("%Y-%m-%d %H:%M:%S")
        message = Message(created, record.levelname, record.levelno, record.getMessage())
        self.messageQueue.put(message)

    def showContextMenu(self, position):
        item = self.treeWidget.currentItem()
        if item:
            contextMenu = QtWidgets.QMenu(self.treeWidget)
            copyAction = contextMenu.addAction("&Copy")
            copyAction.triggered.connect(self.copyToClipboard)
            contextMenu.exec_(self.treeWidget.viewport().mapToGlobal(position))

    def copyToClipboard(self):
        item = self.treeWidget.currentItem()
        if item:
            content = "\t".join(item.text(col) for col in range(self.treeWidget.columnCount()))
            # Set the text to the clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.setText(content)
