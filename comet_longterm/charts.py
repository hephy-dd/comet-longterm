import logging
import math

from PyQt5 import QtCore, QtGui

__all__ = ['IVChartProxy', 'ItChartProxy', 'CtsChartProxy', 'Pt100ChartProxy']

class IVChartProxy:

    def __init__(self, chart, sensors):
        self.chart = chart
        self.chart.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.chart.addValueAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Voltage V")
        self.axisX.setRange(0, 800)

        # Y axis
        self.axisY = self.chart.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")
        self.axisY.setRange(0, 100)

        self.ivSeries = {}
        for sensor in sensors:
            series = self.chart.addLineSeries(self.axisX, self.axisY)
            self.ivSeries[sensor.index] = series
        self.load(sensors)

    def load(self, sensors):
        for sensor in sensors:
            series = self.ivSeries.get(sensor.index)
            series.data().clear()
            series.setName(format(sensor.name))
            series.setPen(QtGui.QColor(sensor.color))
            series.setVisible(sensor.enabled)

    def append(self, reading):
        voltage = reading.get('U')
        for channel in reading.get('channels').values():
            series = self.ivSeries.get(channel.get('index'))
            series.data().append(voltage, channel.get('I') * 1000 * 1000) # a to uA
        if self.chart.isZoomed():
            self.chart.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.chart.fit()

class ItChartProxy:

    def __init__(self, chart, sensors):
        self.chart = chart
        self.chart.legend().setAlignment(QtCore.Qt.AlignRight)

        self.axisX = self.chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")

        self.axisY = self.chart.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Current uA")
        self.axisY.setRange(0, 100)

        self.itSeries = {}
        for sensor in sensors:
            series = self.chart.addLineSeries(self.axisX, self.axisY)
            self.itSeries[sensor.index] = series
        self.load(sensors)

    def load(self, sensors):
        for sensor in sensors:
            series = self.itSeries.get(sensor.index)
            series.data().clear()
            series.setName(format(sensor.name))
            series.setPen(QtGui.QColor(sensor.color))
            series.setVisible(sensor.enabled)

    def append(self, reading):
        ts = reading.get('time')
        for channel in reading.get('channels').values():
            series = self.itSeries.get(channel.get('index'))
            series.data().append(ts, channel.get('I') * 1000 * 1000) # A to uA
        if self.chart.isZoomed():
            self.chart.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.chart.fit()

class CtsChartProxy:

    def __init__(self, chart):
        self.chart = chart
        self.chart.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setTickCount(3)

        # Y axis left
        self.axisY1 = self.chart.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY1.setTitleText("Temp")
        self.axisY1.setRange(0, 180)
        self.axisY1.setLinePenColor(QtCore.Qt.red)

        self.ctsTempSeries = self.chart.addLineSeries(self.axisX, self.axisY1)
        self.ctsTempSeries.setName("Temp")
        self.ctsTempSeries.setPen(self.axisY1.linePenColor())

        # Y axis right
        self.axisY2 = self.chart.addValueAxis(QtCore.Qt.AlignRight)
        self.axisY2.setRange(0, 100)
        self.axisY2.setLinePenColor(QtCore.Qt.blue)

        self.ctsHumidSeries = self.chart.addLineSeries(self.axisX, self.axisY2)
        self.ctsHumidSeries.setName("Humid")
        self.ctsHumidSeries.setPen(self.axisY2.linePenColor())

        # another Y axis left
        self.axisY3 = self.chart.addCategoryAxis(QtCore.Qt.AlignRight)
        self.axisY3.setRange(0, 1)
        self.axisY3.append("Off", 0)
        self.axisY3.append("On", 1)
        self.axisY3.setLinePenColor(QtCore.Qt.magenta)

        self.ctsProgramSeries = self.chart.addLineSeries(self.axisX, self.axisY3)
        self.ctsProgramSeries.setName("Program")
        self.ctsProgramSeries.setPen(self.axisY3.linePenColor())

    def append(self, reading):
        ts = reading.get('time')
        self.ctsTempSeries.data().append(ts, reading.get('temp'))
        self.ctsHumidSeries.data().append(ts, reading.get('humid'))
        self.ctsProgramSeries.data().append(ts, reading.get('program') != 0)
        if self.chart.isZoomed():
            self.chart.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.chart.fit()

class Pt100ChartProxy:

    def __init__(self, chart, sensors):
        self.chart = chart
        self.chart.legend().setAlignment(QtCore.Qt.AlignRight)

        # X axis
        self.axisX = self.chart.addDateTimeAxis(QtCore.Qt.AlignBottom)
        self.axisX.setTitleText("Time")
        self.axisX.setTickCount(3)

        # Y axis left
        self.axisY = self.chart.addValueAxis(QtCore.Qt.AlignLeft)
        self.axisY.setTitleText("Temp")
        self.axisY.setRange(0, 100)

        self.pt100Series = {}
        for sensor in sensors:
            series = self.chart.addLineSeries(self.axisX, self.axisY)
            self.pt100Series[sensor.index] = series
        self.load(sensors)

    def load(self, sensors):
        for sensor in sensors:
            series = self.pt100Series[sensor.index]
            series.data().clear()
            series.setName(format(sensor.name))
            series.setPen(QtGui.QColor(sensor.color))
            series.setVisible(sensor.enabled)

    def append(self, reading):
        ts = reading.get('time')
        for channel in reading.get('channels').values():
            series = self.pt100Series.get(channel.get('index'))
            if channel.get('temp') is not None:
                # watch out!
                if not math.isnan(channel.get('temp')):
                    series.data().append(ts, channel.get('temp'))
        if self.chart.isZoomed():
            self.chart.updateAxis(self.axisX, self.axisX.min(), self.axisX.max())
        else:
            self.chart.fit()
