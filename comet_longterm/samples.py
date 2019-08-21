from PyQt5 import QtCore, QtGui, QtWidgets

DistinctColors = [
    (230, 25, 75),
    (60, 180, 75),
    (255, 225, 25),
    (0, 130, 200),
    (245, 130, 48),
    (145, 30, 180),
    (70, 240, 240),
    (240, 50, 230),
    (210, 245, 60),
    (250, 190, 190),
    (0, 128, 128),
    (230, 190, 255),
    (170, 110, 40),
    (255, 250, 200),
    (128, 0, 0),
    (170, 255, 195),
    (128, 128, 0),
    (255, 215, 180),
    (0, 0, 128),
    (128, 128, 128),
    (255, 255, 255),
    (0, 0, 0),
]
"""List of distinct colors used for plots."""

class Sample(object):
    """Represents state of a sample."""

    class State:
        OK = "OK"
        COMPL_ERR = "COMPL_ERR"

    def __init__(self, index):
        self.index = index
        self.enabled = False
        self.color = (255, 255, 255)
        self.name = "Unnamed{}".format(index)
        self.status = self.State.OK
        self.current = None
        self.temp = None

class SampleManager(object):

    def __init__(self, count):
        self.samples = []
        for i in range(count):
            sample = Sample(i+1)
            sample.color = DistinctColors[i]
            self.samples.append(sample)

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, key):
        return self.samples[key]

    def __iter__(self):
        return iter(self.samples)

class SampleModel(QtCore.QAbstractTableModel):

    columns = ["", "Name", "Status", "Current (uA)", "PT100 Temp. (°C)"]

    class Column:
        Enabled = 0
        Name = 1
        State = 2
        Current = 3
        Temp = 4

    def __init__(self, samples, parent=None):
        super().__init__(parent)
        self.samples = samples

    def rowCount(self, parent):
        return len(self.samples)

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
        if index.isValid():
            sample = self.samples[index.row()]

            if role == QtCore.Qt.DisplayRole:
                if index.column() == self.Column.Name:
                    return sample.name
                elif index.column() == self.Column.State:
                    if sample.enabled:
                        return sample.status
                elif index.column() == self.Column.Current:
                    if sample.enabled:
                        return sample.current

            elif role == QtCore.Qt.DecorationRole:
                if index.column() == self.Column.Enabled:
                    return QtGui.QColor(*sample.color)

            elif role == QtCore.Qt.ForegroundRole:
                if index.column() == self.Column.State:
                    if sample.status == sample.State.OK:
                        return QtGui.QBrush(QtCore.Qt.darkGreen)
                    return QtGui.QBrush(QtCore.Qt.darkRed)

            elif role == QtCore.Qt.CheckStateRole:
                if index.column() == self.Column.Enabled:
                    return [QtCore.Qt.Unchecked, QtCore.Qt.Checked][sample.enabled]

            elif role == QtCore.Qt.EditRole:
                if index.column() == self.Column.Name:
                    return sample.name

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid():
            sample = self.samples[index.row()]

            if role == QtCore.Qt.CheckStateRole:
                if index.column() == self.Column.Enabled:
                    sample.enabled = (value == QtCore.Qt.Checked)
                    self.dataChanged.emit(index, self.createIndex(index.row(), self.Column.Temp))
                    return True

            elif role == QtCore.Qt.EditRole:
                if index.column() == self.Column.Name:
                    sample.name = format(value)
                    self.dataChanged.emit(index, index)
                    return True
                if index.column() == self.Column.Current:
                    sample.current = value
                    self.dataChanged.emit(index, index)
                    return True
        return False

    def flags(self, index):
        flags = super().flags(index)
        if index.column() == self.Column.Enabled:
            return flags | QtCore.Qt.ItemIsUserCheckable
        if index.column() == self.Column.Name:
            return flags | QtCore.Qt.ItemIsEditable
        return flags
