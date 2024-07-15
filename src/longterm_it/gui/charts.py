import math
from typing import Iterable

from PyQt5 import QtCore, QtGui
from QCharted import Chart

__all__ = [
    "IVChart",
    "ItChart",
    "CtsChart",
    "IVTempChart",
    "ItTempChart",
    "ShuntBoxChart",
    "IVSourceChart",
    "ItSourceChart",
]

DateTimeFormat = "dd-MM-yyyy<br/>&#160;&#160;&#160;hh:mm:ss"


class IVChart(Chart):

    def __init__(self, sensors: Iterable) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.addValueAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Voltage V (abs)")
        self.axisX.setRange(0, 800)

        # Y axis
        self.axisY = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")
        self.axisY.setRange(0, 100)

        self.ivSeries = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axisX, self.axisY)
            self.ivSeries[sensor.index] = series
        self.load(sensors)

    def load(self, sensors: Iterable) -> None:
        for sensor in sensors:
            series = self.ivSeries.get(sensor.index)
            if series is not None:
                series.data().clear()
                series.setName(format(sensor.name))
                series.setPen(QtGui.QColor(sensor.color))
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        voltage = abs(reading.get("U", math.nan))  # absolute (can be negative)
        for channel in reading.get("channels", {}).values():
            series = self.ivSeries.get(channel.get("index"))
            if series is not None:
                series.data().append(voltage, channel.get("I", math.nan) * 1000 * 1000)  # a to uA
        if self.isZoomed():
            self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.fit()


class ItChart(Chart):

    def __init__(self, sensors: Iterable) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        self.axisX = self.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setFormat(DateTimeFormat)

        self.axisY = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")
        self.axisY.setRange(0, 100)

        self.itSeries: dict = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axisX, self.axisY)
            self.itSeries[sensor.index] = series
        self.load(sensors)

    def load(self, sensors: Iterable) -> None:
        for sensor in sensors:
            series = self.itSeries.get(sensor.index)
            if series is not None:
                series.data().clear()
                series.setName(format(sensor.name))
                series.setPen(QtGui.QColor(sensor.color))
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        for channel in reading.get("channels", {}).values():
            series = self.itSeries.get(channel.get("index"))
            if series is not None:
                series.data().append(ts, channel.get("I", math.nan) * 1000 * 1000)  # A to uA
        if self.isZoomed():
            self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.fit()


class CtsChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setTickCount(3)
        self.axisX.setFormat(DateTimeFormat)

        # Y axis left
        self.axisY1 = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY1.setTitleText("Temp")
        self.axisY1.setRange(0, 180)
        self.axisY1.setLinePenColor(QtCore.Qt.red)

        self.ctsTempSeries = self.addLineSeries(self.axisX, self.axisY1)
        self.ctsTempSeries.setName("Temp")
        self.ctsTempSeries.setPen(self.axisY1.linePenColor())

        # Y axis right
        self.axisY2 = self.addValueAxis(QtCore.Qt.AlignRight)
        self.axisY2.setRange(0, 100)
        self.axisY2.setLinePenColor(QtCore.Qt.blue)

        self.ctsHumidSeries = self.addLineSeries(self.axisX, self.axisY2)
        self.ctsHumidSeries.setName("Humid")
        self.ctsHumidSeries.setPen(self.axisY2.linePenColor())

        # another Y axis left
        self.axisY3 = self.addCategoryAxis(QtCore.Qt.AlignRight)
        self.axisY3.setRange(0, 1)
        self.axisY3.append("Off", 0.5)
        self.axisY3.append("On", 1)
        self.axisY3.setLinePenColor(QtCore.Qt.magenta)

        self.ctsProgramSeries = self.addLineSeries(self.axisX, self.axisY3)
        self.ctsProgramSeries.setName("Running")
        self.ctsProgramSeries.setPen(self.axisY3.linePenColor())

    def reset(self) -> None:
        self.ctsTempSeries.data().clear()
        self.ctsHumidSeries.data().clear()
        self.ctsProgramSeries.data().clear()
        self.fit()

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        self.ctsTempSeries.data().append(ts, reading.get("temp", math.nan))
        self.ctsHumidSeries.data().append(ts, reading.get("humid", math.nan))
        self.ctsProgramSeries.data().append(ts, reading.get("running", False) != 0)
        if self.isZoomed():
            self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.fit()


class IVTempChart(Chart):

    def __init__(self, sensors: Iterable) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setTickCount(3)
        self.axisX.setFormat(DateTimeFormat)

        # Y axis left
        self.axisY = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Temp")
        self.axisY.setRange(0, 100)

        self.tempSeries: dict = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axisX, self.axisY)
            self.tempSeries[sensor.index] = series
        self.load(sensors)

    def load(self, sensors: Iterable) -> None:
        for sensor in sensors:
            series = self.tempSeries.get(sensor.index)
            if series is not None:
                series.data().clear()
                series.setName(format(sensor.name))
                series.setPen(QtGui.QColor(sensor.color))
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        for channel in reading.get("channels", {}).values():
            series = self.tempSeries.get(channel.get("index"))
            if series is not None:
                if channel.get("temp", math.nan) is not None:
                    # watch out!
                    if not math.isnan(channel.get("temp", math.nan)):
                        series.data().append(ts, channel.get("temp", math.nan))
        self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())


class ItTempChart(IVTempChart):

    ...


class ShuntBoxChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setTickCount(3)
        self.axisX.setFormat(DateTimeFormat)

        # Y axis left
        self.axisY1 = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY1.setTitleText("Seconds")

        # Y axis right
        self.axisY2 = self.addValueAxis(QtCore.Qt.AlignRight)
        self.axisY2.setTitleText("Bytes")

        self.uptimeSeries = self.addLineSeries(self.axisX, self.axisY1)
        self.uptimeSeries.setName("Uptime")

        self.memorySeries = self.addLineSeries(self.axisX, self.axisY2)
        self.memorySeries.setName("Memory")

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        self.uptimeSeries.data().append(ts, reading.get("shuntbox", {}).get("uptime", 0))
        self.memorySeries.data().append(ts, reading.get("shuntbox", {}).get("memory", 0))
        if self.isZoomed():
            self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.fit()


class IVSourceChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.addValueAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Voltage V (abs)")
        self.axisX.setRange(0, 800)

        # Y axis
        self.axisY = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")

        self.ivSeries = self.addLineSeries(self.axisX, self.axisY)
        self.ivSeries.setName("SMU")
        self.ivSeries.setPen(QtGui.QColor("red"))

    def append(self, reading: dict) -> None:
        voltage = abs(reading.get("U", math.nan))  # absolute (can be negative)
        current = reading.get("I", math.nan) * 1e6  # A to uA
        self.ivSeries.data().append(voltage, current)
        self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())

    def reset(self) -> None:
        self.ivSeries.data().clear()
        self.fit()


class ItSourceChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        self.legend().setAlignment(QtCore.Qt.AlignRight)

        self.axisX = self.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setFormat(DateTimeFormat)

        self.axisY = self.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")

        self.itSeries = self.addLineSeries(self.axisX, self.axisY)
        self.itSeries.setName("SMU")
        self.itSeries.setPen(QtGui.QColor("red"))

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        current = reading.get("I", math.nan) * 1e6  # A to uA
        self.itSeries.data().append(ts, current)
        self.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())

    def reset(self) -> None:
        self.itSeries.data().clear()
        self.fit()
