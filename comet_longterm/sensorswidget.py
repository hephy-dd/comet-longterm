from PyQt5 import QtCore, QtGui, QtWidgets

from comet import UiLoaderMixin, DeviceMixin

Colors = (
    '#2a7fff', '#5fd3bc', '#ffd42a', '#ff7f2a', '#ff1f2a', '#ff40d9',
    '#aa00d4', '#5f00ff', '#5fe556', '#00aa44', '#217321'
)
"""List of distinct colors used for plots."""

SensorCount = 10

class SensorsWidget(QtWidgets.QWidget, UiLoaderMixin, DeviceMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.sensors = SensorManager(SensorCount)
        self.model = SensorsModel(self.sensors)
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.resizeColumnsToContents()
        self.ui.tableView.resizeRowsToContents()

class SensorsModel(QtCore.QAbstractTableModel):

    columns = (
        "Sensor",
        "Status",
        "Current (uA)",
        "Temp. (°C)",
        "Resistivity (Ohm)",
    )

    class Column:
        Name = 0
        State = 1
        Current = 2
        Temp = 3
        Resistivity = 4

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
            elif index.column() == self.Column.Current:
                if sensor.enabled:
                    return sensor.current
            elif index.column() == self.Column.Temp:
                if sensor.enabled:
                    return sensor.temp
            elif index.column() == self.Column.Resistivity:
                if sensor.enabled:
                    return sensor.resistivity

        elif role == QtCore.Qt.DecorationRole:
            if index.column() == self.Column.Name:
                return QtGui.QColor(sensor.color)

        elif role == QtCore.Qt.ForegroundRole:
            if index.column() == self.Column.State:
                if sensor.status == sensor.State.OK:
                    return QtGui.QBrush(QtCore.Qt.darkGreen)
                return QtGui.QBrush(QtCore.Qt.darkRed)

        elif role == QtCore.Qt.CheckStateRole:
            if index.column() == self.Column.Name:
                return [QtCore.Qt.Unchecked, QtCore.Qt.Checked][sensor.enabled]

        elif role == QtCore.Qt.EditRole:
            if index.column() == self.Column.Name:
                return sensor.name

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if not index.isValid():
            return
        sensor = self.sensors[index.row()]

        if role == QtCore.Qt.CheckStateRole:
            if index.column() == self.Column.Name:
                sensor.enabled = (value == QtCore.Qt.Checked)
                self.dataChanged.emit(index, self.createIndex(index.row(), self.Column.Temp))
                self.sensors.storeSettings()
                return True

        elif role == QtCore.Qt.EditRole:
            if index.column() == self.Column.Name:
                sensor.name = format(value)
                self.dataChanged.emit(index, index)
                self.sensors.storeSettings()
                return True

        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == self.Column.Name:
            return flags | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEditable
        return flags

class Sensor(object):
    """Represents state of a sensor."""

    class State:
        OK = "OK"
        COMPL_ERR = "COMPL_ERR"

    def __init__(self, index):
        self.index = index
        self.enabled = False
        self.color = "#000000"
        self.name = "Unnamed{}".format(index)
        self.status = self.State.OK
        self.current = None
        self.temp = None
        self.resistivity = 1000000.0

class SensorManager(object):

    def __init__(self, count):
        self.sensors = []
        for i in range(count):
            sensor = Sensor(i+1)
            sensor.color = Colors[i]
            self.sensors.append(sensor)
        self.loadSettings()

    def loadSettings(self):
        settings = QtCore.QSettings()
        data = settings.value('sensors', {})
        for sensor in self.sensors:
            if sensor.index in data:
                sensor.enabled = data.get(sensor.index).get('enabled', False)
                sensor.name = data.get(sensor.index).get('name', "Unnamed{}".format(sensor.index))

    def storeSettings(self):
        data = {}
        for sensor in self.sensors:
            data[sensor.index] = {}
            data[sensor.index]['enabled'] = sensor.enabled
            data[sensor.index]['name'] = sensor.name
        settings = QtCore.QSettings()
        settings.setValue('sensors', data)

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
