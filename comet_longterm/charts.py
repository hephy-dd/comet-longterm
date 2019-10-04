import logging

from PyQt5 import QtCore, QtGui, QtChart

class LineSeries(QtChart.QLineSeries):
    """Base class for line series."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setUseOpenGL(True)

class SensorLineSeries(LineSeries):
    """Line series class for a sensor."""

    def __init__(self, sensor, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.load(sensor)

    def load(self, sensor):
        self.setName(format(sensor.name))
        self.setColor(QtGui.QColor(sensor.color))
        self.setVisible(sensor.enabled)

class Chart(QtChart.QChart):
    """Base class for charts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.legend().setAlignment(QtCore.Qt.AlignRight)
        self.setMargins(QtCore.QMargins(2, 2, 2, 2))

class IVChart(Chart):

    def __init__(self, sensors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # X axis
        self.axisX = QtChart.QValueAxis()
        self.axisX.setTitleText("Voltage V")
        #self.axisX.setRange(0, 800)
        self.addAxis(self.axisX, QtCore.Qt.AlignBottom)

        # Y axis
        self.axisY = QtChart.QValueAxis()
        self.axisY.setTitleText("Current uA")
        #self.axisY.setRange(0, 100)
        self.addAxis(self.axisY, QtCore.Qt.AlignLeft)

        self.ivSeries = []
        for sensor in sensors:
            series = SensorLineSeries(sensor)
            self.addSeries(series)
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)
            self.ivSeries.append(series)

    def load(self, sensors):
        for i, sensor in enumerate(sensors):
            series = self.ivSeries[i]
            series.clear()
            series.load(sensor)

    def append(self, readings):
        for i, reading in enumerate(readings.get('singles')):
            logging.info("IVChart %s %s", i, reading)
            self.ivSeries[i].append(reading.get('u'), reading.get('i') * 1000000)
        # minimum = self.ivSeries[0].at(0).x()
        # maximum = self.ivSeries[0].at(self.ivSeries[0].count()-1).x()
        # self.axisX.setRange(minimum, maximum)
        # minimum = self.ivSeries[0].at(0).y()
        # maximum = self.ivSeries[0].at(self.ivSeries[0].count()-1).y()
        # self.axisY.setRange(minimum, maximum)

class ItChart(Chart):

    def __init__(self, sensors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.axisX = QtChart.QDateTimeAxis()
        self.axisX.setTitleText("Time")
        self.axisX.setFormat("HH:mm:ss<br/>yyyy-MM-dd")
        self.addAxis(self.axisX, QtCore.Qt.AlignBottom)

        self.axisY = QtChart.QValueAxis()
        self.axisY.setTitleText("Current uA")
        self.axisY.setRange(0, 100)
        self.addAxis(self.axisY, QtCore.Qt.AlignLeft)

        self.itSeries = []
        for sensor in sensors:
            series = SensorLineSeries(sensor)
            self.addSeries(series)
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)
            self.itSeries.append(series)

    def load(self, sensors):
        for i, sensor in enumerate(sensors):
            series = self.itSeries[i]
            series.clear()
            series.load(sensor)

    def append(self, readings):
        for i, reading in enumerate(readings.get('singles')):
            time = readings.get('time') * 1000
            self.itSeries[i].append(time, reading.get('i') * 1000000)

class CtsChart(Chart):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # X axis
        self.axisX = QtChart.QDateTimeAxis()
        self.axisX.setTitleText("Time")
        self.axisX.setFormat("HH:mm:ss<br/>yyyy-MM-dd")
        self.axisX.setTickCount(3)
        self.addAxis(self.axisX, QtCore.Qt.AlignBottom)

        # Y axis left
        self.axisY1 = QtChart.QValueAxis()
        self.axisY1.setTitleText("Temp")
        self.axisY1.setRange(0, 180)
        self.addAxis(self.axisY1, QtCore.Qt.AlignLeft)

        self.ctsTempSeries = LineSeries()
        self.ctsTempSeries.setName("Temp")
        self.addSeries(self.ctsTempSeries)
        self.ctsTempSeries.attachAxis(self.axisX)
        self.ctsTempSeries.attachAxis(self.axisY1)

        # Y axis right
        self.axisY2 = QtChart.QValueAxis()
        self.axisY2.setRange(0, 100)
        self.addAxis(self.axisY2, QtCore.Qt.AlignRight)

        self.ctsHumidSeries = LineSeries()
        self.ctsHumidSeries.setName("Humid")
        self.addSeries(self.ctsHumidSeries)
        self.ctsHumidSeries.attachAxis(self.axisX)
        self.ctsHumidSeries.attachAxis(self.axisY2)

        # another Y axis left
        self.axisY3 = QtChart.QCategoryAxis()
        self.axisY3.setRange(0, 1)
        self.axisY3.append("Off", 0)
        self.axisY3.append("On", 1)
        self.addAxis(self.axisY3, QtCore.Qt.AlignRight)

        self.ctsProgramSeries = LineSeries()
        self.ctsProgramSeries.setName("Program")
        self.addSeries(self.ctsProgramSeries)
        self.ctsProgramSeries.attachAxis(self.axisX)
        self.ctsProgramSeries.attachAxis(self.axisY3)

    def append(self, reading):
        ts = reading.get('time') * 1000
        self.ctsTempSeries.append(ts, reading.get('temp'))
        self.ctsHumidSeries.append(ts, reading.get('humid'))
        self.ctsProgramSeries.append(ts, reading.get('program') != 0)
        minimum = QtCore.QDateTime.fromMSecsSinceEpoch(self.ctsTempSeries.at(0).x())
        maximum = QtCore.QDateTime.fromMSecsSinceEpoch(self.ctsTempSeries.at(self.ctsTempSeries.count()-1).x())
        self.axisX.setRange(minimum, maximum)

class Pt100Chart(Chart):

    def __init__(self, sensors, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # X axis
        self.axisX = QtChart.QDateTimeAxis()
        self.axisX.setTitleText("Time")
        self.axisX.setFormat("HH:mm:ss<br/>yyyy-MM-dd")
        self.axisX.setTickCount(3)
        self.addAxis(self.axisX, QtCore.Qt.AlignBottom)

        # Y axis left
        self.axisY = QtChart.QValueAxis()
        self.axisY.setTitleText("Temp")
        self.axisY.setRange(0, 100)
        self.addAxis(self.axisY, QtCore.Qt.AlignLeft)

        self.pt100Series = []
        for sensor in sensors:
            series = SensorLineSeries(sensor)
            self.addSeries(series)
            series.attachAxis(self.axisX)
            series.attachAxis(self.axisY)
            self.pt100Series.append(series)