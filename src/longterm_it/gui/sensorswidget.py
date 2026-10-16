import logging
from typing import ClassVar, Final

from PySide6 import QtCore, QtGui, QtWidgets

from ..sensor import Sensor
from ..settings import SettingsAdapter
from ..utils import auto_unit

SENSOR_COLORS: Final[list[str]] = [
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

CALIBRATED_RESISTORS: Final[list[float]] = [
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

SENSOR_COUNT: Final[int] = 10

logger = logging.getLogger(__name__)


class HVDelegate(QtWidgets.QItemDelegate):
    STATES: ClassVar = (
        "OFF",
        "ON",
    )

    def createEditor(self, parent, option, index):
        editor = QtWidgets.QComboBox(parent)
        editor.addItems(self.STATES)
        editor.currentIndexChanged.connect(self.currentIndexChanged)
        return editor

    def setEditorData(self, editor, index) -> None:
        if editor is None:
            return
        pos = self.STATES.index(index.data(QtCore.Qt.ItemDataRole.DisplayRole))
        editor.setCurrentIndex(pos)

    def setModelData(self, editor, model, index) -> None:
        if editor is None:
            return
        if model is None:
            return
        editorIndex = editor.currentIndex()
        model.setData(index, bool(editorIndex))

    @QtCore.Slot()
    def currentIndexChanged(self) -> None:
        self.commitData.emit(self.sender())


class SensorsWidget(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)

        self.sensors = SensorManager(SENSOR_COUNT)
        self.model = SensorsModel(self.sensors)

        self.setWindowTitle("Sensors")

        self.tableView = QtWidgets.QTableView()
        self.tableView.setProperty("showDropIndicator", False)
        self.tableView.setDragDropOverwriteMode(False)
        self.tableView.setSelectionMode(
            QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
        )
        self.tableView.setSelectionBehavior(
            QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tableView.setCornerButtonEnabled(False)
        horizontal_header = self.tableView.horizontalHeader()
        if horizontal_header is not None:
            horizontal_header.setHighlightSections(False)
            horizontal_header.setStretchLastSection(True)
        self.tableView.setModel(self.model)
        self.tableView.resizeColumnsToContents()
        self.tableView.resizeRowsToContents()
        self.tableView.setColumnWidth(0, 172)
        self.tableView.setColumnWidth(1, 64)
        self.tableView.setColumnWidth(3, 96)
        self.tableView.setColumnWidth(4, 64)
        self.tableView.setItemDelegateForColumn(2, HVDelegate())
        self.tableView.setSizeAdjustPolicy(
            QtWidgets.QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents
        )
        self.tableView.doubleClicked.connect(self.editTableItem)

        layout = QtWidgets.QGridLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.tableView, 0, 0, 1, 1)

        self.verticalResizeTableView()

    def verticalResizeTableView(self) -> None:
        """Resize table view to vertical content height."""
        rowTotalHeight = 0
        vertical_header = self.tableView.verticalHeader()
        if vertical_header is not None:
            count = vertical_header.count()
            for i in range(count):
                if not vertical_header.isSectionHidden(i):
                    rowTotalHeight += vertical_header.sectionSize(i)
        horizontal_scroll_bar = self.tableView.horizontalScrollBar()
        if horizontal_scroll_bar is not None:
            # if not self.tableView.horizontalScrollBar().isHidden():
            rowTotalHeight += horizontal_scroll_bar.height()
        horizontal_header = self.tableView.horizontalHeader()
        if horizontal_header is not None:
            # if not self.tableView.horizontalHeader().isHidden():
            rowTotalHeight += horizontal_header.height()
        self.tableView.setMinimumHeight(rowTotalHeight)

    def dataChanged(self) -> None:
        self.model.dataChanged.emit(
            self.model.createIndex(0, 1),
            self.model.createIndex(len(self.sensors), 4),
        )

    def editTableItem(self, index: QtCore.QModelIndex) -> None:
        if index.isValid():
            try:
                sensor = self.sensors.sensors[index.row()]
                if index.column() == SensorsModel.Column.TemperatureOffset:
                    value, ok = QtWidgets.QInputDialog.getDouble(
                        self,
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
                        self.sensors.writeSettings()
            except Exception:
                logger.exception("Failed to write settings")

    def readSettings(self) -> None:
        self.sensors.readSettings()

    def writeSettings(self) -> None:
        self.sensors.writeSettings()


class SensorsModel(QtCore.QAbstractTableModel):
    COLUMNS: ClassVar = (
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

    def __init__(self, sensors: "SensorManager"):
        super().__init__()
        self.sensors = sensors

    def rowCount(self, parent=None) -> int:
        return len(self.sensors)

    def columnCount(self, parent=None) -> int:
        return len(self.COLUMNS)

    def headerData(
        self, section, orientation, role: int = QtCore.Qt.ItemDataRole.DisplayRole
    ):
        if orientation == QtCore.Qt.Orientation.Horizontal:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return self.COLUMNS[section]
            elif role == QtCore.Qt.ItemDataRole.ToolTipRole:
                if section == self.Column.Temperature:
                    return "Temperature"
                elif section == self.Column.TemperatureOffset:
                    return "Temperature Offset"
                elif section == self.Column.Resistivity:
                    return "Calibration Resistivitiy"
        elif orientation == QtCore.Qt.Orientation.Vertical:
            if role == QtCore.Qt.ItemDataRole.DisplayRole:
                return section + 1

    def data(self, index, role: int = QtCore.Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return

        sensor = self.sensors[index.row()]

        if role == QtCore.Qt.ItemDataRole.DisplayRole:
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
                        return f"{sensor.temperature:.2f} °C"
            elif index.column() == self.Column.TemperatureOffset:
                return f"{sensor.temperature_offset:+.2f} °C"
            elif index.column() == self.Column.Resistivity:
                return f"{sensor.resistivity:d} Ohm"

        elif role == QtCore.Qt.ItemDataRole.DecorationRole:
            if index.column() == self.Column.Name:
                return QtGui.QColor(sensor.color)

        elif role == QtCore.Qt.ItemDataRole.ForegroundRole:
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
                    return QtGui.QBrush(QtCore.Qt.darkGray)  # type: ignore

        elif role == QtCore.Qt.ItemDataRole.TextAlignmentRole:
            if index.column() == self.Column.Current:
                return QtCore.Qt.AlignRight  # type: ignore
            elif index.column() == self.Column.Temperature:
                return QtCore.Qt.AlignRight  # type: ignore
            elif index.column() == self.Column.TemperatureOffset:
                return QtCore.Qt.AlignRight  # type: ignore
            elif index.column() == self.Column.Resistivity:
                return QtCore.Qt.AlignRight  # type: ignore

        elif role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if index.column() == self.Column.Name:
                return [QtCore.Qt.CheckState.Unchecked, QtCore.Qt.CheckState.Checked][
                    sensor.enabled
                ]

        elif role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == self.Column.Name:
                return sensor.name
            if index.column() == self.Column.HV:
                return sensor.hv
            if index.column() == self.Column.Resistivity:
                return sensor.resistivity

    def setData(
        self, index, value, role: int = QtCore.Qt.ItemDataRole.EditRole
    ) -> bool:
        if not index.isValid():
            return False
        sensor = self.sensors[index.row()]

        if role == QtCore.Qt.ItemDataRole.CheckStateRole:
            if index.column() == self.Column.Name:
                sensor.enabled = value == QtCore.Qt.CheckState.Checked
                self.dataChanged.emit(
                    index, self.createIndex(index.row(), self.Column.Temperature)
                )
                self.sensors.writeSettings()
                return True

        elif role == QtCore.Qt.ItemDataRole.EditRole:
            if index.column() == self.Column.Name:
                sensor.name = format(value)
                self.dataChanged.emit(index, index)
                self.sensors.writeSettings()
                return True
            # if index.column() == self.Column.HV:
            #     sensor.hv = value
            #     self.dataChanged.emit(index, index)
            #     self.sensors.writeSettings()
            #     return True
            # if index.column() == self.Column.Resistivity:
            #     sensor.resistivity = format(value)
            #     self.dataChanged.emit(index, index)
            #     self.sensors.writeSettings()
            #     return True

        return False

    def flags(self, index):
        flags = super().flags(index)
        # sensor = self.sensors[index.row()]
        if self.sensors.isEditable():
            if index.column() == self.Column.Name:
                return (
                    flags
                    | QtCore.Qt.ItemFlag.ItemIsUserCheckable
                    | QtCore.Qt.ItemFlag.ItemIsEditable
                )
            # if index.column() == self.Column.HV:
            #     if sensor.enabled:
            #         return flags | QtCore.Qt.ItemIsEditable
            # if index.column() == self.Column.Resistivity:
            #     return flags | QtCore.Qt.ItemIsEditable
        return flags


class SensorManager:
    def __init__(self, count: int) -> None:
        self.sensors: list[Sensor] = []
        for i in range(count):
            sensor = Sensor(i + 1)
            sensor.color = SENSOR_COLORS[i]
            sensor.resistivity = CALIBRATED_RESISTORS[i]
            self.sensors.append(sensor)
        self.setEditable(True)

    def readSettings(self) -> None:
        settings = SettingsAdapter(QtCore.QSettings())
        data = settings.get("sensors", {}, dict)
        for i, sensor in enumerate(self.sensors):
            if sensor.index in data:
                sensor.enabled = data.get(sensor.index, {}).get("enabled", False)
                sensor.name = data.get(sensor.index, {}).get(
                    "name", f"Unnamed{sensor.index}"
                )
                sensor.temperature_offset = float(
                    data.get(sensor.index, {}).get("temperature_offset", 0)
                )
                sensor.resistivity = int(
                    data.get(sensor.index, {}).get(
                        "resistivity", CALIBRATED_RESISTORS[i]
                    )
                )

    def writeSettings(self) -> None:
        data: dict = {}
        for sensor in self.sensors:
            data[sensor.index] = {}
            data[sensor.index]["enabled"] = bool(sensor.enabled)
            data[sensor.index]["name"] = str(sensor.name)
            data[sensor.index]["temperature_offset"] = float(sensor.temperature_offset)
            data[sensor.index]["resistivity"] = int(sensor.resistivity)
        settings = SettingsAdapter(QtCore.QSettings())
        settings.set("sensors", data)

    def isEditable(self) -> bool:
        return self.__editable

    def setEditable(self, value):
        self.__editable = bool(value)

    def __len__(self) -> int:
        return len(self.sensors)

    def __getitem__(self, key):
        return self.sensors[key]

    def __iter__(self):
        return iter(self.sensors)
