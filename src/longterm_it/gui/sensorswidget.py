import logging

from PyQt5 import QtCore, QtGui, QtWidgets

from ..sensor import Sensor
from ..utils import auto_unit

Colors: list = [
    "#2a7fff",
    "#5fd3bc",
    "#ffd42a",
    "#ff7f2a",
    "#ff1f2a",
    "#ff40d9",
    "#aa00d4",
    "#5f00ff",
    "#5fe556",
    "#00aa44",
    "#217321",
]
"""List of distinct colors used for plots."""

CalibratedResistors: list = [
    470160,
    471085,
    469315,
    471981,
    470772,
    469546,
    470727,
    470488,
    469947,
    469314,
]
"""List of default calibrated resistors in Ohm."""

SensorCount: int = 10

logger = logging.getLogger(__name__)


class HVDelegate(QtWidgets.QItemDelegate):

    States = ["OFF", "ON"]

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.addItems(self.States)
        editor.currentIndexChanged.connect(self.currentIndexChanged)
        return editor

    def setEditorData(self, editor, index):
        pos = self.States.index(index.data(QtCore.Qt.DisplayRole))
        editor.setCurrentIndex(pos)

    def setModelData(self, editor, model, index):
        editorIndex = editor.currentIndex()
        model.setData(index, bool(editorIndex))

    @QtCore.pyqtSlot()
    def currentIndexChanged(self):
        self.commitData.emit(self.sender())


class SensorsWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sensors = SensorManager(SensorCount)
        self.model = SensorsModel(self.sensors)

        self.setWindowTitle("Sensors")

        self.tableView = QtWidgets.QTableView()
        self.tableView.setProperty("showDropIndicator", False)
        self.tableView.setDragDropOverwriteMode(False)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.tableView.setCornerButtonEnabled(False)
        self.tableView.horizontalHeader().setHighlightSections(False)
        self.tableView.horizontalHeader().setStretchLastSection(True)
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setColumnWidth(0, 172)
        self.tableView.setColumnWidth(1, 64)
        self.tableView.setColumnWidth(3, 96)
        self.tableView.setColumnWidth(4, 64)
        self.tableView.setItemDelegateForColumn(2, HVDelegate())
        self.tableView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.AdjustToContents
        )
        self.tableView.doubleClicked.connect(self.editTableItem)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tableView, 0, 0, 1, 1)

        self.verticalResizeTableView()

    def verticalResizeTableView(self):
        """Resize table view to vertical content height."""
        rowTotalHeight = 0
        count = self.tableView.verticalHeader().count()
        for i in range(count):
            if not self.tableView.verticalHeader().isSectionHidden(i):
                rowTotalHeight += self.tableView.verticalHeader().sectionSize(i)
        # if not self.tableView.horizontalScrollBar().isHidden():
        rowTotalHeight += self.tableView.horizontalScrollBar().height()
        # if not self.tableView.horizontalHeader().isHidden():
        rowTotalHeight += self.tableView.horizontalHeader().height()
        self.tableView.setMinimumHeight(rowTotalHeight)

    def dataChanged(self):
        self.model.dataChanged.emit(
            self.model.createIndex(0, 1),
            self.model.createIndex(len(self.sensors), 4),
        )

    def editTableItem(self, index: QtCore.QModelIndex) -> None:
        if index.isValid():
            try:
                sensor = self.sensors.sensors[index.row()]
                if index.column() == SensorsModel.Column.TemperatureOffset:
                    value, ok = QtWidgets.QInputDialog.getDouble(self,
                        "Edit Sample",
                        "Temperature Offset (°C)",
                        sensor.temperature_offset,
                        -256.0,
                        +256.0,
                        2,
                    )
                    if ok:
                        sensor.temperature_offset = value
                        self.dataChanged()  # HACK keep updated
                        self.sensors.storeSettings()
            except Exception as exc:
                logger.exception(exc)


class SensorsModel(QtCore.QAbstractTableModel):

    columns = (
        "Sensor",
        "Status",
        "HV",
        "Current",
        "Temp.",
        "Temp. Off.",
        "Calib.",
    )

    class Column:
        Name = 0
        State = 1
        HV = 2
        Current = 3
        Temperature = 4
        TemperatureOffset = 5
        Resistivity = 6

    def __init__(self, sensors, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sensors = sensors

    def rowCount(self, parent):
        return len(self.sensors)

    def columnCount(self, parent):
        return len(self.columns)

    def headerData(self, section, orientation, role):
        if orientation == QtCore.Qt.Horizontal:
            if role == QtCore.Qt.DisplayRole:
                return self.columns[section]
        elif orientation == QtCore.Qt.Vertical:
            if role == QtCore.Qt.DisplayRole:
                return section + 1

    def data(self, index, role):
        if not index.isValid():
            return

        sensor = self.sensors[index.row()]

        if role == QtCore.Qt.DisplayRole:
            if index.column() == self.Column.Name:
                return sensor.name
            elif index.column() == self.Column.State:
                if sensor.enabled:
                    return sensor.status
            elif index.column() == self.Column.HV:
                if sensor.enabled:
                    if sensor.hv is None:
                        return "N/A"
                    return "ON" if sensor.hv else "OFF"
            elif index.column() == self.Column.Current:
                if sensor.enabled:
                    if not sensor.current is None:
                        return auto_unit(sensor.current, "A", decimals=3)
            elif index.column() == self.Column.Temperature:
                if sensor.enabled:
                    if not sensor.temperature is None:
                        return "{:.2f} °C".format(sensor.temperature)
            elif index.column() == self.Column.TemperatureOffset:
                return "{:+.2f} °C".format(sensor.temperature_offset)
            elif index.column() == self.Column.Resistivity:
                return "{:d} Ohm".format(sensor.resistivity)

        elif role == QtCore.Qt.DecorationRole:
            if index.column() == self.Column.Name:
                return QtGui.QColor(sensor.color)

        elif role == QtCore.Qt.ForegroundRole:
            if index.column() == self.Column.State:
                if sensor.status == sensor.State.OK:
                    return QtGui.QBrush(QtGui.QColor("#00bb00"))
                return QtGui.QBrush(QtGui.QColor("#bb0000"))
            if index.column() == self.Column.HV:
                if sensor.hv:
                    return QtGui.QBrush(QtGui.QColor("#00bb00"))
                return QtGui.QBrush(QtGui.QColor("#bb0000"))
            else:
                if not sensor.enabled:
                    return QtGui.QBrush(QtCore.Qt.darkGray)

        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == self.Column.Name:
                return [QtCore.Qt.Unchecked, QtCore.Qt.Checked][sensor.enabled]

        elif role == QtCore.Qt.EditRole:
            if index.column() == self.Column.Name:
                return sensor.name
            if index.column() == self.Column.HV:
                return sensor.hv
            if index.column() == self.Column.Resistivity:
                return sensor.resistivity

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return
        sensor = self.sensors[index.row()]

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == self.Column.Name:
                sensor.enabled = value == QtCore.Qt.Checked
                self.dataChanged.emit(
                    index, self.createIndex(index.row(), self.Column.Temperature)
                )
                self.sensors.storeSettings()
                return True

        elif role == QtCore.Qt.EditRole:
            if index.column() == self.Column.Name:
                sensor.name = format(value)
                self.dataChanged.emit(index, index)
                self.sensors.storeSettings()
                return True
            # if index.column() == self.Column.HV:
            #     sensor.hv = value
            #     self.dataChanged.emit(index, index)
            #     self.sensors.storeSettings()
            #     return True
            # if index.column() == self.Column.Resistivity:
            #     sensor.resistivity = format(value)
            #     self.dataChanged.emit(index, index)
            #     self.sensors.storeSettings()
            #     return True

        return False

    def flags(self, index):
        flags = super().flags(index)
        sensor = self.sensors[index.row()]
        if self.sensors.isEditable():
            if index.column() == self.Column.Name:
                return flags | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable
            # if index.column() == self.Column.HV:
            #     if sensor.enabled:
            #         return flags | QtCore.Qt.ItemIsEditable
            # if index.column() == self.Column.Resistivity:
            #     return flags | QtCore.Qt.ItemIsEditable
        return flags


class SensorManager:

    def __init__(self, count):
        self.sensors = []
        for i in range(count):
            sensor = Sensor(i + 1)
            sensor.color = Colors[i]
            sensor.resistivity = CalibratedResistors[i]
            self.sensors.append(sensor)
        self.loadSettings()
        self.setEditable(True)

    def loadSettings(self) -> None:
        settings = QtCore.QSettings()
        data = settings.value("sensors", {})
        for i, sensor in enumerate(self.sensors):
            if sensor.index in data:
                sensor.enabled = data.get(sensor.index, {}).get("enabled", False)
                sensor.name = data.get(sensor.index, {}).get(
                    "name", "Unnamed{}".format(sensor.index)
                )
                sensor.temperature_offset = float(
                    data.get(sensor.index, {}).get("temperature_offset", 0)
                )
                sensor.resistivity = int(
                    data.get(sensor.index, {}).get("resistivity", CalibratedResistors[i])
                )

    def storeSettings(self) -> None:
        data: dict = {}
        for sensor in self.sensors:
            data[sensor.index] = {}
            data[sensor.index]["enabled"] = bool(sensor.enabled)
            data[sensor.index]["name"] = str(sensor.name)
            data[sensor.index]["temperature_offset"] = float(sensor.temperature_offset)
            data[sensor.index]["resistivity"] = int(sensor.resistivity)
        settings = QtCore.QSettings()
        settings.setValue("sensors", data)

    def isEditable(self):
        return self.__editable

    def setEditable(self, value):
        self.__editable = bool(value)

    def __len__(self):
        return len(self.sensors)

    def __getitem__(self, key):
        return self.sensors[key]

    def __iter__(self):
        return iter(self.sensors)
