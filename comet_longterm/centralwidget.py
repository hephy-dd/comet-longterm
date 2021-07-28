from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtChart

from comet import UiLoaderMixin

from .charts import IVChart, ItChart, CtsChart, IVTempChart, ItTempChart
from .charts import ShuntBoxChart, IVSourceChart, ItSourceChart

class CentralWidget(QtWidgets.QWidget, UiLoaderMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()
        self.createCharts()

        self.statusWidget().setVoltage(None)
        self.statusWidget().setCurrent(None)
        # TODO implement measurement timer
        self.controlsWidget().ui.itDurationSpinBox.setEnabled(False)

    def createCharts(self):
        self.ivChart = IVChart(self.sensors())
        self.ui.ivChartView.setChart(self.ivChart)
        self.itChart = ItChart(self.sensors())
        self.ui.itChartView.setChart(self.itChart)
        self.ctsChart = CtsChart()
        self.ui.ctsChartView.setChart(self.ctsChart)
        self.ivTempChart = IVTempChart(self.sensors())
        self.ui.ivTempChartView.setChart(self.ivTempChart)
        self.itTempChart = ItTempChart(self.sensors())
        self.ui.itTempChartView.setChart(self.itTempChart)
        self.shuntBoxChart = ShuntBoxChart()
        self.ui.shuntBoxChartView.setChart(self.shuntBoxChart)
        self.ivSourceChart = IVSourceChart()
        self.ui.ivSourceChartView.setChart(self.ivSourceChart)
        self.itSourceChart = ItSourceChart()
        self.ui.itSourceChartView.setChart(self.itSourceChart)

        def ivRangeChanged(minimum, maximum):
            self.ivSourceChart.fit()
            self.ivSourceChart.axisX.setRange(minimum, maximum)
            self.ivTempChart.fit()
        self.ivChart.axisX.rangeChanged.connect(ivRangeChanged)

        def itRangeChanged(minimum, maximum):
            self.itTempChart.fit()
            self.itTempChart.axisX.setRange(minimum, maximum)
            self.itSourceChart.fit()
            self.itSourceChart.axisX.setRange(minimum, maximum)
        self.itChart.axisX.rangeChanged.connect(itRangeChanged)

    def sensors(self):
        """Returns sensors manager."""
        return self.sensorsWidget().sensors

    def sensorsWidget(self):
        """Returns sensors widget."""
        return self.ui.sensorsWidget

    def controlsWidget(self):
        """Returns controls widget."""
        return self.ui.controlsWidget

    def statusWidget(self):
        """Returns status widget."""
        return self.ui.statusWidget

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.ui.topTabWidget.setCurrentIndex(0)
        self.ui.bottomTabWidget.setCurrentIndex(1) # switch to IV temperature

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.ui.topTabWidget.setCurrentIndex(1)
        self.ui.bottomTabWidget.setCurrentIndex(2) # switch to It temperature

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, reading):
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get('channels')[sensor.index].get('I')
                sensor.temperature = reading.get('channels')[sensor.index].get('temp')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.ivTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.ivSourceChart.append(reading)
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onMeasItReading(self, reading):
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get('channels')[sensor.index].get('I')
                sensor.temperature = reading.get('channels')[sensor.index].get('temp')
        self.sensorsWidget().dataChanged() # HACK keep updated
        self.itTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.itSourceChart.append(reading)
        self.itChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onSmuReading(self, reading):
        self.statusWidget().setVoltage(reading.get('U'))
        self.statusWidget().setCurrent(reading.get('I'))

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.controlsWidget().onHalted()
        self.statusWidget().setCurrent(None)
        self.statusWidget().setVoltage(None)
        self.statusWidget().setCurrent(None)
        self.sensors().setEditable(True)
