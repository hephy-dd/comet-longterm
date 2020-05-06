from PyQt5 import QtCore, QtGui, QtWidgets

from comet import UiLoaderMixin, DeviceMixin

from .utils import auto_unit

Colors = (
    '#2a7fff', '#5fd3bc', '#ffd42a', '#ff7f2a', '#ff1f2a', '#ff40d9',
    '#aa00d4', '#5f00ff', '#5fe556', '#00aa44', '#217321'
)
"""List of distinct colors used for plots."""

CalibratedResistors = (
    470160, 471085, 469315, 471981, 470772, 469546, 470727, 470488, 469947, 469314
)
"""List of default calibrated resistors in Ohm."""

SensorCount = 10

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

class SensorsWidget(QtWidgets.QWidget, UiLoaderMixin, DeviceMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.sensors = SensorManager(SensorCount)
        self.model = SensorsModel(self.sensors)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.resizeRowsToContents()
        self.ui.tableView.setColumnWidth(0, 172)
        self.ui.tableView.setColumnWidth(1, 64)
        self.ui.tableView.setColumnWidth(3, 96)
        self.ui.tableView.setColumnWidth(4, 64)
        self.ui.tableView.setItemDelegateForColumn(2, HVDelegate())
        self.verticalResizeTableView()

    def verticalResizeTableView(self):
        """Resize table view to vertical content height."""
        rowTotalHeight = 0
        count = self.ui.tableView.verticalHeader().count()
        for i in range(count):
            if not self.ui.tableView.verticalHeader().isSectionHidden(i):
                rowTotalHeight += self.ui.tableView.verticalHeader().sectionSize(i)
        # if not self.ui.tableView.horizontalScrollBar().isHidden():
        #     rowTotalHeight += self.ui.tableView.horizontalScrollBar().height()
        # if not self.ui.tableView.horizontalHeader().isHidden():
        #     rowTotalHeight += self.ui.tableView.horizontalHeader().height()
        self.ui.tableView.setMinimumHeight(rowTotalHeight)

    def dataChanged(self):
        self.model.dataChanged.emit(
            self.model.createIndex(0, 1),
            self.model.createIndex(len(self.sensors), 4),
        )

class SensorsModel(QtCore.QAbstractTableModel):

    columns = (
        "Sensor",
        "Status",
        "HV",
        "Current",
        "Temp.",
        "Calib.",
    )

    class Column:
        Name = 0
        State = 1
        HV = 2
        Current = 3
        Temperature = 4
        Resistivity = 5

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
            retrun

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
                        return auto_unit(sensor.current, 'A', decimals=3)
            elif index.column() == self.Column.Temperature:
                if sensor.enabled:
                    if not sensor.temperature is None:
                        return "{} °C".format(sensor.temperature)
            elif index.column() == self.Column.Resistivity:
                return "{} Ohm".format(sensor.resistivity)

        elif role == QtCore.Qt.DecorationRole:
            if index.column() == self.Column.Name:
                return QtGui.QColor(sensor.color)

        elif role == QtCore.Qt.ForegroundRole:
            if index.column() == self.Column.State:
                if sensor.status == sensor.State.OK:
                    return QtGui.QBrush(QtGui.QColor('#00bb00'))
                return QtGui.QBrush(QtGui.QColor('#bb0000'))
            if index.column() == self.Column.HV:
                if sensor.hv:
                    return QtGui.QBrush(QtGui.QColor('#00bb00'))
                return QtGui.QBrush(QtGui.QColor('#bb0000'))
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
                sensor.enabled = (value == QtCore.Qt.Checked)
                self.dataChanged.emit(index, self.createIndex(index.row(), self.Column.Temperature))
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

class Sensor(object):
    """Represents state of a sensor."""

    class State:
        OK = "OK"
        COMPL_ERR = "COMPL"

    def __init__(self, index):
        self.index = index
        self.enabled = False
        self.color = "#000000"
        self.name = "Unnamed{}".format(index)
        self.status = None
        self.hv = None # valid: None, True, False
        self.current = None
        self.temperature = None
        self.resistivity = None

class SensorManager(object):

    def __init__(self, count):
        self.sensors = []
        for i in range(count):
            sensor = Sensor(i+1)
            sensor.color = Colors[i]
            sensor.resistivity = CalibratedResistors[i]
            self.sensors.append(sensor)
        self.loadSettings()
        self.setEditable(True)

    def loadSettings(self):
        settings = QtCore.QSettings()
        data = settings.value('sensors', {})
        for i, sensor in enumerate(self.sensors):
            if sensor.index in data:
                sensor.enabled = data.get(sensor.index).get('enabled', False)
                sensor.name = data.get(sensor.index).get('name', "Unnamed{}".format(sensor.index))
                sensor.resistivity = int(data.get(sensor.index).get('resistivity', CalibratedResistors[i]))

    def storeSettings(self):
        data = {}
        for sensor in self.sensors:
            data[sensor.index] = {}
            data[sensor.index]['enabled'] = bool(sensor.enabled)
            data[sensor.index]['name'] = str(sensor.name)
            data[sensor.index]['resistivity'] = int(sensor.resistivity)
        settings = QtCore.QSettings()
        settings.setValue('sensors', data)

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

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = SensorsWidget()
    w.show()
    app.exec_()
