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
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        # X axis
        self.axis_x = self.addValueAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Voltage V (abs)")
        self.axis_x.setRange(0, 800)

        # Y axis
        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Current uA")
        self.axis_y.setRange(0, 100)

        self.ivSeries = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axis_x, self.axis_y)
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
            self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())
        else:
            self.fit()


class ItChart(Chart):

    def __init__(self, sensors: Iterable) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setFormat(DateTimeFormat)

        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Current uA")
        self.axis_y.setRange(0, 100)

        self.itSeries: dict = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axis_x, self.axis_y)
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
            self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())
        else:
            self.fit()


class CtsChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        # X axis
        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setTickCount(3)
        self.axis_x.setFormat(DateTimeFormat)

        # Y axis left
        self.axis_y1 = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y1.setTitleText("Temp")
        self.axis_y1.setRange(0, 180)
        self.axis_y1.setLinePenColor(QtCore.Qt.red)  # type: ignore

        self.ctsTempSeries = self.addLineSeries(self.axis_x, self.axis_y1)
        self.ctsTempSeries.setName("Temp")
        self.ctsTempSeries.setPen(self.axis_y1.linePenColor())

        # Y axis right
        self.axis_y2 = self.addValueAxis(QtCore.Qt.AlignRight)  # type: ignore
        self.axis_y2.setRange(0, 100)
        self.axis_y2.setLinePenColor(QtCore.Qt.blue)  # type: ignore

        self.ctsHumidSeries = self.addLineSeries(self.axis_x, self.axis_y2)
        self.ctsHumidSeries.setName("Humid")
        self.ctsHumidSeries.setPen(self.axis_y2.linePenColor())

        # another Y axis left
        self.axis_y3 = self.addCategoryAxis(QtCore.Qt.AlignRight)  # type: ignore
        self.axis_y3.setRange(0, 1)
        self.axis_y3.append("Off", 0.5)
        self.axis_y3.append("On", 1)
        self.axis_y3.setLinePenColor(QtCore.Qt.magenta)  # type: ignore

        self.ctsProgramSeries = self.addLineSeries(self.axis_x, self.axis_y3)
        self.ctsProgramSeries.setName("Running")
        self.ctsProgramSeries.setPen(self.axis_y3.linePenColor())

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
            self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())
        else:
            self.fit()


class IVTempChart(Chart):

    def __init__(self, sensors: Iterable) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        # X axis
        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setTickCount(3)
        self.axis_x.setFormat(DateTimeFormat)

        # Y axis left
        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Temp")
        self.axis_y.setRange(0, 100)

        self.tempSeries: dict = {}
        for sensor in sensors:
            series = self.addLineSeries(self.axis_x, self.axis_y)
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
        self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())


class ItTempChart(IVTempChart):

    ...


class ShuntBoxChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        # X axis
        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setTickCount(3)
        self.axis_x.setFormat(DateTimeFormat)

        # Y axis left
        self.axis_y1 = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y1.setTitleText("Seconds")

        # Y axis right
        self.axis_y2 = self.addValueAxis(QtCore.Qt.AlignRight)  # type: ignore
        self.axis_y2.setTitleText("Bytes")

        self.uptimeSeries = self.addLineSeries(self.axis_x, self.axis_y1)
        self.uptimeSeries.setName("Uptime")

        self.memorySeries = self.addLineSeries(self.axis_x, self.axis_y2)
        self.memorySeries.setName("Memory")

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        self.uptimeSeries.data().append(ts, reading.get("shuntbox", {}).get("uptime", 0))
        self.memorySeries.data().append(ts, reading.get("shuntbox", {}).get("memory", 0))
        if self.isZoomed():
            self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())
        else:
            self.fit()


class IVSourceChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        # X axis
        self.axis_x = self.addValueAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Voltage V (abs)")
        self.axis_x.setRange(0, 800)

        # Y axis
        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Current uA")

        self.ivSeries = self.addLineSeries(self.axis_x, self.axis_y)
        self.ivSeries.setName("SMU")
        self.ivSeries.setPen(QtGui.QColor("red"))

    def append(self, reading: dict) -> None:
        voltage = abs(reading.get("U", math.nan))  # absolute (can be negative)
        current = reading.get("I", math.nan) * 1e6  # A to uA
        self.ivSeries.data().append(voltage, current)
        self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())

    def reset(self) -> None:
        self.ivSeries.data().clear()
        self.fit()


class ItSourceChart(Chart):

    def __init__(self) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setFormat(DateTimeFormat)

        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Current uA")

        self.itSeries = self.addLineSeries(self.axis_x, self.axis_y)
        self.itSeries.setName("SMU")
        self.itSeries.setPen(QtGui.QColor("red"))

    def append(self, reading: dict) -> None:
        ts = reading.get("time", 0)
        current = reading.get("I", math.nan) * 1e6  # A to uA
        self.itSeries.data().append(ts, current)
        self.updateAxis(self.axis_x, self.axis_x.min(), self.axis_x.max())

    def reset(self) -> None:
        self.itSeries.data().clear()
        self.fit()
