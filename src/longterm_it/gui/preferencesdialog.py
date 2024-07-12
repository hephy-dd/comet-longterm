from typing import Any, Optional

from PyQt5 import QtCore, QtWidgets

from ..utils import escape_string, unescape_string


class ResourcesTab(QtWidgets.QWidget):

    DefaultReadTermination = "\r\n"
    DefaultWriteTermination = "\r\n"
    DefaultTimeout = 2000
    DefaultVisaLibrary = "@py"

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Resources"))
        self.treeWidget = QtWidgets.QTreeWidget()
        self.treeWidget.setColumnCount(2)
        item = self.treeWidget.headerItem()
        if item:
            item.setText(0, self.tr("Resource"))
            item.setText(1, self.tr("Value"))
        self.treeWidget.itemDoubleClicked.connect(
            lambda item, column: self.editResource()
        )
        self.treeWidget.itemSelectionChanged.connect(self.selectionChanged)
        self.editButton = QtWidgets.QPushButton(self.tr("&Edit"))
        self.editButton.setEnabled(False)
        self.editButton.clicked.connect(self.editResource)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.treeWidget, 0, 0, 2, 1)
        layout.addWidget(self.editButton, 0, 1)
        layout.addItem(QtWidgets.QSpacerItem(0, 0), 1, 1)
        self.setLayout(layout)

    def resources(self) -> dict:
        """Returns dictionary of resource options."""
        root = self.treeWidget.topLevelItem(0)
        resources: dict = {}
        for i in range(self.treeWidget.topLevelItemCount()):
            item = self.treeWidget.topLevelItem(i)
            if not item:
                continue
            name = item.text(0)
            options = {}
            for j in range(item.childCount()):
                child = item.child(j)
                key = child.text(0)
                value: Any = child.text(1)
                # Escape special characters
                if key in ["read_termination", "write_termination"]:
                    value = unescape_string(value)
                # Convert integers
                if key in ["timeout"]:
                    try:
                        value = int(value)
                    except ValueError:
                        value = self.DefaultTimeout
                options[key] = value
            resources[name] = options
        return resources

    def setResources(self, resources: dict) -> None:
        """Set dictionary of resource options."""
        self.treeWidget.clear()
        items: list = []
        for name, options in resources.items():
            item = QtWidgets.QTreeWidgetItem([name])
            item.addChild(
                QtWidgets.QTreeWidgetItem(
                    ["resource_name", options.get("resource_name")]
                )
            )
            item.addChild(
                QtWidgets.QTreeWidgetItem(
                    [
                        "read_termination",
                        escape_string(
                            options.get("read_termination", self.DefaultReadTermination)
                        ),
                    ]
                )
            )
            item.addChild(
                QtWidgets.QTreeWidgetItem(
                    [
                        "write_termination",
                        escape_string(
                            options.get(
                                "write_termination", self.DefaultWriteTermination
                            )
                        ),
                    ]
                )
            )
            item.addChild(
                QtWidgets.QTreeWidgetItem(
                    ["timeout", format(options.get("timeout", self.DefaultTimeout))]
                )
            )
            item.addChild(
                QtWidgets.QTreeWidgetItem(
                    [
                        "visa_library",
                        options.get("visa_library", self.DefaultVisaLibrary),
                    ]
                )
            )
            self.treeWidget.insertTopLevelItem(0, item)
            self.treeWidget.expandItem(item)
        self.treeWidget.resizeColumnToContents(0)

    @QtCore.pyqtSlot()
    def editResource(self) -> None:
        item = self.treeWidget.currentItem()
        if item and item.parent():
            text, ok = QtWidgets.QInputDialog.getText(
                self,
                self.tr("Resource {}").format(item.parent().text(0)),
                item.text(0),
                QtWidgets.QLineEdit.Normal,
                item.text(1),
            )
            if ok:
                item.setText(1, text)

    @QtCore.pyqtSlot()
    def selectionChanged(self) -> None:
        item = self.treeWidget.currentItem()
        if item:
            self.editButton.setEnabled(item.parent() is not None)


class OperatorsTab(QtWidgets.QWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Operators"))
        self.listWidget = QtWidgets.QListWidget()
        self.listWidget.itemDoubleClicked.connect(self.editOperator)
        self.listWidget.itemSelectionChanged.connect(self.selectionChanged)
        self.addButton = QtWidgets.QPushButton(self.tr("&Add"))
        self.addButton.clicked.connect(self.addOperator)
        self.editButton = QtWidgets.QPushButton(self.tr("&Edit"))
        self.editButton.setEnabled(False)
        self.editButton.clicked.connect(self.editOperator)
        self.removeButton = QtWidgets.QPushButton(self.tr("&Remove"))
        self.removeButton.setEnabled(False)
        self.removeButton.clicked.connect(self.removeOperator)
        layout = QtWidgets.QGridLayout()
        layout.addWidget(self.listWidget, 0, 0, 4, 1)
        layout.addWidget(self.addButton, 0, 1)
        layout.addWidget(self.editButton, 1, 1)
        layout.addWidget(self.removeButton, 2, 1)
        layout.addItem(QtWidgets.QSpacerItem(0, 0), 3, 1)
        self.setLayout(layout)

    def operators(self) -> list[str]:
        """Returns list of operators."""
        operators: list[str] = []
        for index in range(self.listWidget.count()):
            item = self.listWidget.item(index)
            if item:
                operators.append(item.text())
        return operators

    def setOperators(self, operators: list[str]) -> None:
        """Set list of operators."""
        self.listWidget.clear()
        for text in operators:
            self.listWidget.addItem(text)

    @QtCore.pyqtSlot()
    def addOperator(self) -> None:
        text, ok = QtWidgets.QInputDialog.getText(
            self, self.tr("Operator"), self.tr("Name"), QtWidgets.QLineEdit.Normal
        )
        if ok and text:
            item = self.listWidget.addItem(text)
            self.listWidget.setCurrentItem(item)

    @QtCore.pyqtSlot()
    def editOperator(self) -> None:
        item = self.listWidget.currentItem()
        if item:
            text, ok = QtWidgets.QInputDialog.getText(
                self,
                self.tr("Operator"),
                self.tr("Name"),
                QtWidgets.QLineEdit.Normal,
                item.text(),
            )
            if ok and text:
                item.setText(text)

    @QtCore.pyqtSlot()
    def removeOperator(self) -> None:
        item = self.listWidget.currentItem()
        if item is not None:
            row = self.listWidget.row(item)
            self.listWidget.takeItem(row)

    @QtCore.pyqtSlot()
    def selectionChanged(self) -> None:
        item = self.listWidget.currentItem()
        self.editButton.setEnabled(item is not None)
        self.removeButton.setEnabled(item is not None)


class PreferencesDialog(QtWidgets.QDialog):

    def __init__(self, resources, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.resources = resources
        self.setWindowTitle(self.tr("Preferences"))
        self.resize(480, 320)
        self.tabWidget = QtWidgets.QTabWidget()
        self.resourcesTab = ResourcesTab()
        self.tabWidget.addTab(self.resourcesTab, self.resourcesTab.windowTitle())
        self.operatorsTab = OperatorsTab()
        self.tabWidget.addTab(self.operatorsTab, self.operatorsTab.windowTitle())
        self.buttonBox = QtWidgets.QDialogButtonBox()
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.addButton(QtWidgets.QDialogButtonBox.Cancel)
        self.buttonBox.addButton(QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.accepted.connect(self.handleAccept)
        self.buttonBox.rejected.connect(self.reject)
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(self.tabWidget)
        layout.addWidget(self.buttonBox)
        self.setLayout(layout)
        self.loadSettings()

    @QtCore.pyqtSlot()
    def handleAccept(self) -> None:
        self.saveSettings()
        QtWidgets.QMessageBox.information(
            self,
            self.tr("Preferences"),
            self.tr("Application restart required for changes to take effect."),
        )
        self.accept()

    def saveSettings(self) -> None:
        settings = QtCore.QSettings()
        settings.setValue("operators", self.operatorsTab.operators())
        settings.setValue("resources2", self.resourcesTab.resources())

    def loadSettings(self) -> None:
        resources = {}
        for name, resource in self.resources.items():
            options = {}
            options["resource_name"] = resource.resource_name
            options["read_termination"] = resource.options.get(
                "read_termination", ResourcesTab.DefaultReadTermination
            )
            options["write_termination"] = resource.options.get(
                "write_termination", ResourcesTab.DefaultWriteTermination
            )
            options["timeout"] = resource.options.get(
                "timeout", ResourcesTab.DefaultTimeout
            )
            options["visa_library"] = resource.visa_library
            resources[name] = options
        # Update default resources with stored settings
        settings = QtCore.QSettings()
        # Migrate old style settings (<= 0.12.x)
        if not settings.value("resources2", {}, dict):
            for name, resource_name in settings.value("resources", {}, dict).items():
                resources.update({name: {"resource_name": resource_name}})
        for name, options in settings.value("resources2", {}, dict).items():
            if name in resources:
                for key, value in options.items():
                    resources[name][key] = value
        self.resourcesTab.setResources(resources)
        operators = settings.value("operators", [], list)
        self.operatorsTab.setOperators(operators)
