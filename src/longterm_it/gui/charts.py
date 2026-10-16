import math
from collections.abc import Iterable
from typing import Final

from PyQt5 import QtChart, QtCore, QtGui

__all__ = [
    "CtsChart",
    "IVChart",
    "IVSourceChart",
    "IVTempChart",
    "ItChart",
    "ItSourceChart",
    "ItTempChart",
    "ShuntBoxChart",
]

DATE_TIME_FORMAT: Final = "dd-MM-yyyy hh:mm:ss"


class Chart(QtChart.QChart):
    """Small convenience layer implemented entirely with QtCharts.

    Charts remain QChart instances suitable for QChartView(chart).
    Timestamp readings are Unix seconds; QDateTimeAxis uses milliseconds.
    """

    def addValueAxis(self, alignment) -> QtChart.QValueAxis:
        axis = QtChart.QValueAxis()
        self.addAxis(axis, alignment)
        return axis

    def addDateTimeAxis(self, alignment) -> QtChart.QDateTimeAxis:
        axis = QtChart.QDateTimeAxis()
        self.addAxis(axis, alignment)
        return axis

    def addCategoryAxis(self, alignment) -> QtChart.QCategoryAxis:
        axis = QtChart.QCategoryAxis()
        self.addAxis(axis, alignment)
        return axis

    def addLineSeries(self, axis_x, axis_y) -> QtChart.QLineSeries:
        series = QtChart.QLineSeries()
        self.addSeries(series)
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
        return series

    @staticmethod
    def _set_axis_range(axis, low, high):
        if low == high:
            margin = max(abs(low) * 0.05, 1.0)
            low -= margin
            high += margin
        if isinstance(axis, QtChart.QDateTimeAxis):
            axis.setRange(
                QtCore.QDateTime.fromMSecsSinceEpoch(round(low)),
                QtCore.QDateTime.fromMSecsSinceEpoch(round(high)),
            )
        else:
            axis.setRange(low, high)

    @staticmethod
    def _axis_bounds(axis):
        if isinstance(axis, QtChart.QDateTimeAxis):
            return axis.min().toMSecsSinceEpoch(), axis.max().toMSecsSinceEpoch()
        return axis.min(), axis.max()

    def updateAxis(self, axis, low=None, high=None):
        """Autoscale axes from visible data, optionally fixing one axis range."""
        if axis is not None and low is not None and high is not None:
            if isinstance(low, QtCore.QDateTime):
                low = low.toMSecsSinceEpoch()
                high = high.toMSecsSinceEpoch()
            self._set_axis_range(axis, low, high)

        fixed_bounds = self._axis_bounds(axis) if axis is not None else None
        for target in self.axes():
            if target is axis or isinstance(target, QtChart.QCategoryAxis):
                continue
            is_x = target in self.axes(QtCore.Qt.Horizontal)  # type: ignore
            values = []
            for series in self.series():
                if not series.isVisible() or target not in series.attachedAxes():
                    continue
                if not isinstance(series, QtChart.QLineSeries):
                    continue
                for point in series.pointsVector():
                    x, y = point.x(), point.y()
                    if not (math.isfinite(x) and math.isfinite(y)):
                        continue
                    if fixed_bounds is not None and axis in series.attachedAxes():
                        coordinate = x if axis in self.axes(QtCore.Qt.Horizontal) else y  # type: ignore
                        if not fixed_bounds[0] <= coordinate <= fixed_bounds[1]:
                            continue
                    values.append(x if is_x else y)
            if values:
                self._set_axis_range(target, min(values), max(values))

    def fit(self):
        """Fit all non-category axes to finite, visible series data."""
        self.updateAxis(None)


def _append(series, x, y) -> None:
    """Qt Charts cannot reliably render NaN points."""
    if x is not None and y is not None and math.isfinite(x) and math.isfinite(y):
        series.append(float(x), float(y))


def _time_ms(ts: float) -> float:
    """Convert Unix seconds to the milliseconds required by QDateTimeAxis."""
    return float(ts) * 1000


def _set_color(series, color) -> None:
    pen = series.pen()
    pen.setColor(QtGui.QColor(color))
    series.setPen(pen)


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
                series.clear()
                series.setName(format(sensor.name))
                _set_color(series, sensor.color)
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        voltage = abs(reading.get("U", math.nan))  # absolute (can be negative)
        for channel in reading.get("channels", {}).values():
            series = self.ivSeries.get(channel.get("index"))
            if series is not None:
                _append(
                    series, voltage, channel.get("I", math.nan) * 1000 * 1000
                )  # a to uA
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
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
        self.axis_x.setFormat(DATE_TIME_FORMAT)

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
                series.clear()
                series.setName(format(sensor.name))
                _set_color(series, sensor.color)
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        ts = _time_ms(reading.get("time", 0))
        for channel in reading.get("channels", {}).values():
            series = self.itSeries.get(channel.get("index"))
            if series is not None:
                _append(series, ts, channel.get("I", math.nan) * 1000 * 1000)  # A to uA
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
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
        self.axis_x.setFormat(DATE_TIME_FORMAT)

        # Y axis left
        self.axis_y1 = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y1.setTitleText("Temp")
        self.axis_y1.setRange(0, 180)
        self.axis_y1.setLinePenColor(QtCore.Qt.red)  # type: ignore

        self.ctsTempSeries = self.addLineSeries(self.axis_x, self.axis_y1)
        self.ctsTempSeries.setName("Temp")
        _set_color(self.ctsTempSeries, self.axis_y1.linePenColor())

        # Y axis right
        self.axis_y2 = self.addValueAxis(QtCore.Qt.AlignRight)  # type: ignore
        self.axis_y2.setRange(0, 100)
        self.axis_y2.setLinePenColor(QtCore.Qt.blue)  # type: ignore

        self.ctsHumidSeries = self.addLineSeries(self.axis_x, self.axis_y2)
        self.ctsHumidSeries.setName("Humid")
        _set_color(self.ctsHumidSeries, self.axis_y2.linePenColor())

        # another Y axis left
        self.axis_y3 = self.addCategoryAxis(QtCore.Qt.AlignRight)  # type: ignore
        self.axis_y3.setRange(0, 1)
        self.axis_y3.append("Off", 0.5)
        self.axis_y3.append("On", 1)
        self.axis_y3.setLinePenColor(QtCore.Qt.magenta)  # type: ignore

        self.ctsProgramSeries = self.addLineSeries(self.axis_x, self.axis_y3)
        self.ctsProgramSeries.setName("Running")
        _set_color(self.ctsProgramSeries, self.axis_y3.linePenColor())

    def reset(self) -> None:
        self.ctsTempSeries.clear()
        self.ctsHumidSeries.clear()
        self.ctsProgramSeries.clear()
        self.fit()

    def append(self, reading: dict) -> None:
        ts = _time_ms(reading.get("time", 0))
        _append(self.ctsTempSeries, ts, reading.get("temp", math.nan))
        _append(self.ctsHumidSeries, ts, reading.get("humid", math.nan))
        _append(self.ctsProgramSeries, ts, reading.get("running", False) != 0)
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
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
        self.axis_x.setFormat(DATE_TIME_FORMAT)

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
                series.clear()
                series.setName(format(sensor.name))
                _set_color(series, sensor.color)
                series.setVisible(sensor.enabled)
        self.fit()

    def append(self, reading: dict) -> None:
        ts = _time_ms(reading.get("time", 0))
        for channel in reading.get("channels", {}).values():
            series = self.tempSeries.get(channel.get("index"))
            if series is not None:
                if channel.get("temp", math.nan) is not None:
                    # watch out!
                    if not math.isnan(channel.get("temp", math.nan)):
                        _append(series, ts, channel.get("temp", math.nan))
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
        else:
            self.fit()


class ItTempChart(IVTempChart): ...


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
        self.axis_x.setFormat(DATE_TIME_FORMAT)

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
        ts = _time_ms(reading.get("time", 0))
        _append(self.uptimeSeries, ts, reading.get("shuntbox", {}).get("uptime", 0))
        _append(self.memorySeries, ts, reading.get("shuntbox", {}).get("memory", 0))
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
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
        _set_color(self.ivSeries, "red")

    def append(self, reading: dict) -> None:
        voltage = abs(reading.get("U", math.nan))  # absolute (can be negative)
        current = reading.get("I", math.nan) * 1e6  # A to uA
        _append(self.ivSeries, voltage, current)
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
        else:
            self.fit()

    def reset(self) -> None:
        self.ivSeries.clear()
        self.fit()


class ItSourceChart(Chart):
    def __init__(self) -> None:
        super().__init__()
        legend = self.legend()
        if legend is not None:
            legend.setAlignment(QtCore.Qt.AlignRight)  # type: ignore

        self.axis_x = self.addDateTimeAxis(QtCore.Qt.AlignBottom)  # type: ignore
        self.axis_x.setTitleText("Time")
        self.axis_x.setFormat(DATE_TIME_FORMAT)

        self.axis_y = self.addValueAxis(QtCore.Qt.AlignLeft)  # type: ignore
        self.axis_y.setTitleText("Current uA")

        self.itSeries = self.addLineSeries(self.axis_x, self.axis_y)
        self.itSeries.setName("SMU")
        _set_color(self.itSeries, "red")

    def append(self, reading: dict) -> None:
        ts = _time_ms(reading.get("time", 0))
        current = reading.get("I", math.nan) * 1e6  # A to uA
        _append(self.itSeries, ts, current)
        if self.isZoomed():
            self.updateAxis(self.axis_x, *self._axis_bounds(self.axis_x))
        else:
            self.fit()

    def reset(self) -> None:
        self.itSeries.clear()
        self.fit()
