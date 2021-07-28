import os
from PyQt5 import QtCore
from PyQt5 import QtWidgets

from comet import ResourceMixin

__all__ = ['PreferencesDialog']

class PreferencesDialog(QtWidgets.QDialog, ResourceMixin):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModal(True)
        self.gridLayout = QtWidgets.QGridLayout(self)
        self.gridLayout.setObjectName("gridLayout")
        self.buttonBox = QtWidgets.QDialogButtonBox(self)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout.addWidget(self.buttonBox, 2, 0, 1, 1)
        self.tabWidget = QtWidgets.QTabWidget(self)
        self.tabWidget.setObjectName("tabWidget")
        self.generalTab = QtWidgets.QWidget()
        self.generalTab.setObjectName("generalTab")
        self.gridLayout_5 = QtWidgets.QGridLayout(self.generalTab)
        self.gridLayout_5.setObjectName("gridLayout_5")
        spacerItem = QtWidgets.QSpacerItem(20, 136, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_5.addItem(spacerItem, 1, 0, 1, 1)
        self.visaGroupBox = QtWidgets.QGroupBox(self.generalTab)
        self.visaGroupBox.setObjectName("visaGroupBox")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.visaGroupBox)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.visaComboBox = QtWidgets.QComboBox(self.visaGroupBox)
        self.visaComboBox.setEditable(True)
        self.visaComboBox.setObjectName("visaComboBox")
        self.visaComboBox.addItem("")
        self.visaComboBox.addItem("")
        self.gridLayout_6.addWidget(self.visaComboBox, 0, 0, 1, 1)
        self.gridLayout_5.addWidget(self.visaGroupBox, 0, 0, 1, 1)
        self.tabWidget.addTab(self.generalTab, "")
        self.operatorTab = QtWidgets.QWidget()
        self.operatorTab.setObjectName("operatorTab")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.operatorTab)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.operatorListWidget = QtWidgets.QListWidget(self.operatorTab)
        self.operatorListWidget.setObjectName("operatorListWidget")
        self.gridLayout_2.addWidget(self.operatorListWidget, 0, 0, 4, 1)
        spacerItem1 = QtWidgets.QSpacerItem(20, 103, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_2.addItem(spacerItem1, 3, 1, 1, 1)
        self.addOperatorPushButton = QtWidgets.QPushButton(self.operatorTab)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.addOperatorPushButton.sizePolicy().hasHeightForWidth())
        self.addOperatorPushButton.setSizePolicy(sizePolicy)
        self.addOperatorPushButton.setObjectName("addOperatorPushButton")
        self.gridLayout_2.addWidget(self.addOperatorPushButton, 0, 1, 1, 1)
        self.editOperatorPushButton = QtWidgets.QPushButton(self.operatorTab)
        self.editOperatorPushButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.editOperatorPushButton.sizePolicy().hasHeightForWidth())
        self.editOperatorPushButton.setSizePolicy(sizePolicy)
        self.editOperatorPushButton.setObjectName("editOperatorPushButton")
        self.gridLayout_2.addWidget(self.editOperatorPushButton, 1, 1, 1, 1)
        self.removeOperatorPushButton = QtWidgets.QPushButton(self.operatorTab)
        self.removeOperatorPushButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.removeOperatorPushButton.sizePolicy().hasHeightForWidth())
        self.removeOperatorPushButton.setSizePolicy(sizePolicy)
        self.removeOperatorPushButton.setObjectName("removeOperatorPushButton")
        self.gridLayout_2.addWidget(self.removeOperatorPushButton, 2, 1, 1, 1)
        self.tabWidget.addTab(self.operatorTab, "")
        self.resourcesTab = QtWidgets.QWidget()
        self.resourcesTab.setObjectName("resourcesTab")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.resourcesTab)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.resourcesTableWidget = QtWidgets.QTableWidget(self.resourcesTab)
        self.resourcesTableWidget.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.resourcesTableWidget.setProperty("showDropIndicator", False)
        self.resourcesTableWidget.setDragDropOverwriteMode(False)
        self.resourcesTableWidget.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.resourcesTableWidget.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.resourcesTableWidget.setWordWrap(False)
        self.resourcesTableWidget.setObjectName("resourcesTableWidget")
        self.resourcesTableWidget.setColumnCount(2)
        self.resourcesTableWidget.setRowCount(0)
        item = QtWidgets.QTableWidgetItem()
        self.resourcesTableWidget.setHorizontalHeaderItem(0, item)
        item = QtWidgets.QTableWidgetItem()
        self.resourcesTableWidget.setHorizontalHeaderItem(1, item)
        self.resourcesTableWidget.horizontalHeader().setStretchLastSection(True)
        self.resourcesTableWidget.verticalHeader().setVisible(False)
        self.resourcesTableWidget.verticalHeader().setDefaultSectionSize(18)
        self.resourcesTableWidget.verticalHeader().setMinimumSectionSize(18)
        self.gridLayout_3.addWidget(self.resourcesTableWidget, 0, 0, 2, 1)
        self.editResourcePushButton = QtWidgets.QPushButton(self.resourcesTab)
        self.editResourcePushButton.setEnabled(False)
        self.editResourcePushButton.setObjectName("editResourcePushButton")
        self.gridLayout_3.addWidget(self.editResourcePushButton, 0, 1, 1, 1)
        spacerItem2 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.gridLayout_3.addItem(spacerItem2, 1, 1, 1, 1)
        self.tabWidget.addTab(self.resourcesTab, "")
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 1, 1)

        self.tabWidget.setCurrentIndex(0)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.addOperatorPushButton.clicked.connect(self.addOperator)
        self.editOperatorPushButton.clicked.connect(self.editOperator)
        self.removeOperatorPushButton.clicked.connect(self.removeOperator)
        self.editResourcePushButton.clicked.connect(self.editResource)

        self.setWindowTitle("Preferences")
        self.visaGroupBox.setTitle("VISA Library")
        self.visaComboBox.setItemText(0, "@py")
        self.visaComboBox.setItemText(1, "@sim")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.generalTab), "&General")
        self.addOperatorPushButton.setText("&Add")
        self.editOperatorPushButton.setText("&Edit")
        self.removeOperatorPushButton.setText("&Remove")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.operatorTab), "&Operators")
        self.resourcesTableWidget.setSortingEnabled(True)
        item = self.resourcesTableWidget.horizontalHeaderItem(0)
        item.setText("Name")
        item = self.resourcesTableWidget.horizontalHeaderItem(1)
        item.setText("Resource")
        self.editResourcePushButton.setText("&Edit")
        self.tabWidget.setTabText(self.tabWidget.indexOf(self.resourcesTab), "&Resources")

        self.loadSettings()

    def loadSettings(self):
        # Load settings
        settings = QtCore.QSettings()

        visaLibrary = settings.value('visaLibrary', '@py')
        self.visaComboBox.setCurrentText(visaLibrary)

        operators = settings.value('operators', []) or [] # HACK
        self.operatorListWidget.clear()
        self.operatorListWidget.addItems(operators)

        resources = settings.value('resources', {})
        defaultResources = {}
        for key, value in self.resources.items():
            defaultResources[key] = value.resource_name
        resources.update(defaultResources)
        self.resourcesTableWidget.clearContents()
        self.resourcesTableWidget.setRowCount(len(resources))
        for i, resource in enumerate(resources.items()):
            name, resource = resource
            self.resourcesTableWidget.setItem(i, 0, QtWidgets.QTableWidgetItem(name))
            self.resourcesTableWidget.setItem(i, 1, QtWidgets.QTableWidgetItem(resource))
        self.resourcesTableWidget.resizeRowsToContents()
        self.resourcesTableWidget.resizeColumnsToContents()

        self.operatorListWidget.itemSelectionChanged.connect(self.updateOperatorButtons)
        self.resourcesTableWidget.itemSelectionChanged.connect(self.updateResourceButtons)

    def updateOperatorButtons(self):
        select = self.operatorListWidget.selectionModel()
        self.editOperatorPushButton.setEnabled(select.hasSelection())
        self.removeOperatorPushButton.setEnabled(select.hasSelection())

    def updateResourceButtons(self):
        select = self.resourcesTableWidget.selectionModel()
        self.editResourcePushButton.setEnabled(select.hasSelection())

    def saveSettings(self):
        settings = QtCore.QSettings()
        settings.setValue('visaLibrary', self.visaLibrary())
        settings.setValue('operators', self.operators())
        settings.setValue('resources', self.resources_())

    def accept(self):
        self.saveSettings()
        QtWidgets.QMessageBox.information(self,
            self.tr("Preferences"),
            self.tr("Application restart required for changes to take effect.")
        )
        super().accept()

    def visaLibrary(self):
        """Returns selected state of VISA library combo box."""
        return self.visaComboBox.currentText()

    def operators(self):
        """Returns current list of operators."""
        table = self.operatorListWidget
        operators = []
        for row in range(table.count()):
            operators.append(table.item(row).text())
        return operators

    def resources_(self):
        """Returns list of resources containing name and resource."""
        table = self.resourcesTableWidget
        resources = {}
        for row in range(table.rowCount()):
            name = table.item(row, 0).text()
            resource = table.item(row, 1).text()
            resources[name] = resource
        return resources

    def addOperator(self):
        """Add operator slot."""
        text, ok = QtWidgets.QInputDialog.getText(self,
                self.tr("Operator"),
                self.tr("Name:"),
                QtWidgets.QLineEdit.Normal
            )
        if ok and text:
            table = self.operatorListWidget
            item = table.addItem(text)
            table.setCurrentItem(item)

    def editOperator(self):
        """Edit operator slot."""
        item = self.operatorListWidget.currentItem()
        if item is not None:
            text, ok = QtWidgets.QInputDialog.getText(self,
                self.tr("Operator"),
                self.tr("Name:"),
                QtWidgets.QLineEdit.Normal,
                item.text()
            )
            if ok:
                item.setText(text)

    def removeOperator(self):
        """Remove operator slot."""
        table = self.operatorListWidget
        row = table.currentRow()
        if row is not None:
            table.takeItem(row)

    def editResource(self):
        """Edit device resource slot."""
        table = self.resourcesTableWidget
        row = table.currentRow()
        item = table.item(row, 1)
        if item is not None:
            text, ok = QtWidgets.QInputDialog.getText(self,
                self.tr("Device"),
                self.tr("Resource:"),
                QtWidgets.QLineEdit.Normal,
                item.text()
            )
            if ok:
                item.setText(text)
