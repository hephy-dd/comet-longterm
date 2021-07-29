from PyQt5 import QtCore
from PyQt5 import QtWidgets
from PyQt5 import QtChart

from QCharted import ChartView

from .controlswidget import ControlsWidget
from .sensorswidget import SensorsWidget
from .statuswidget import StatusWidget
from .charts import IVChart, ItChart, CtsChart, IVTempChart, ItTempChart
from .charts import ShuntBoxChart, IVSourceChart, ItSourceChart

class CentralWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Longterm It")

        self.sensorsWidget = SensorsWidget(self)

        self.statusWidget = StatusWidget(self)

        self.controlsWidget = ControlsWidget(self)

        self.ivTab = QtWidgets.QWidget()
        self.ivChartView = ChartView()
        layout = QtWidgets.QGridLayout(self.ivTab)
        layout.addWidget(self.ivChartView, 0, 0, 1, 1)

        self.itTab = QtWidgets.QWidget()
        self.itChartView = ChartView()
        layout = QtWidgets.QGridLayout(self.itTab)
        layout.addWidget(self.itChartView, 0, 0, 1, 1)

        self.topTabWidget = QtWidgets.QTabWidget(self)
        self.topTabWidget.addTab(self.ivTab, "IV Curve")
        self.topTabWidget.addTab(self.itTab, "It Curve")
        self.topTabWidget.setCurrentIndex(0)


        self.ctsTab = QtWidgets.QWidget()
        self.ctsChartView = ChartView(self.ctsTab)
        layout = QtWidgets.QGridLayout(self.ctsTab)
        layout.addWidget(self.ctsChartView, 0, 0, 1, 1)

        self.ivTempTab = QtWidgets.QWidget()
        self.ivTempChartView = ChartView(self.ivTempTab)
        layout = QtWidgets.QGridLayout(self.ivTempTab)
        layout.addWidget(self.ivTempChartView, 0, 0, 1, 1)

        self.itTempTab = QtWidgets.QWidget()
        self.itTempChartView = ChartView(self.itTempTab)
        layout = QtWidgets.QGridLayout(self.itTempTab)
        layout.addWidget(self.itTempChartView, 0, 0, 1, 1)

        self.ivSourceTab = QtWidgets.QWidget()
        self.ivSourceChartView = ChartView(self.ivSourceTab)
        layout = QtWidgets.QGridLayout(self.ivSourceTab)
        layout.addWidget(self.ivSourceChartView, 0, 0, 1, 1)

        self.itSourceTab = QtWidgets.QWidget()
        self.itSourceChartView = ChartView(self.itSourceTab)
        layout = QtWidgets.QGridLayout(self.itSourceTab)
        layout.addWidget(self.itSourceChartView, 0, 0, 1, 1)

        self.shuntBoxTab = QtWidgets.QWidget()
        self.shuntBoxChartView = ChartView(self.shuntBoxTab)
        layout = QtWidgets.QGridLayout(self.shuntBoxTab)
        layout.addWidget(self.shuntBoxChartView, 0, 0, 1, 1)

        self.bottomTabWidget = QtWidgets.QTabWidget(self)
        self.bottomTabWidget.addTab(self.ctsTab, "Chamber")
        self.bottomTabWidget.addTab(self.ivTempTab, "IV Temp.")
        self.bottomTabWidget.addTab(self.itTempTab, "It Temp.")
        self.bottomTabWidget.addTab(self.ivSourceTab, "IV SMU")
        self.bottomTabWidget.addTab(self.itSourceTab, "It SMU")
        self.bottomTabWidget.addTab(self.shuntBoxTab, "Shunt Box")
        self.bottomTabWidget.setCurrentIndex(0)

        self.leftVerticalLayout = QtWidgets.QVBoxLayout()
        self.leftVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.leftVerticalLayout.addWidget(self.sensorsWidget)
        self.leftVerticalLayout.addWidget(self.statusWidget)
        self.leftVerticalLayout.addWidget(self.controlsWidget)
        self.leftVerticalLayout.addStretch()
        self.leftVerticalLayout.setStretch(0, 1)
        self.leftVerticalLayout.setStretch(1, 0)
        self.leftVerticalLayout.setStretch(2, 0)
        self.leftVerticalLayout.setStretch(3, 10)

        self.rightVerticalLayout = QtWidgets.QVBoxLayout()
        self.rightVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.rightVerticalLayout.addWidget(self.topTabWidget)
        self.rightVerticalLayout.addWidget(self.bottomTabWidget)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addLayout(self.leftVerticalLayout)
        layout.addLayout(self.rightVerticalLayout)
        layout.setStretch(0, 5)
        layout.setStretch(1, 6)

        self.createCharts()

        self.statusWidget.setVoltage(None)
        self.statusWidget.setCurrent(None)
        # TODO implement measurement timer
        self.controlsWidget.itDurationSpinBox.setEnabled(False)

        self.controlsWidget.operatorComboBox.setDuplicatesEnabled(False)

    def createCharts(self):
        self.ivChart = IVChart(self.sensors())
        self.ivChartView.setChart(self.ivChart)
        self.itChart = ItChart(self.sensors())
        self.itChartView.setChart(self.itChart)
        self.ctsChart = CtsChart()
        self.ctsChartView.setChart(self.ctsChart)
        self.ivTempChart = IVTempChart(self.sensors())
        self.ivTempChartView.setChart(self.ivTempChart)
        self.itTempChart = ItTempChart(self.sensors())
        self.itTempChartView.setChart(self.itTempChart)
        self.shuntBoxChart = ShuntBoxChart()
        self.shuntBoxChartView.setChart(self.shuntBoxChart)
        self.ivSourceChart = IVSourceChart()
        self.ivSourceChartView.setChart(self.ivSourceChart)
        self.itSourceChart = ItSourceChart()
        self.itSourceChartView.setChart(self.itSourceChart)

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
        return self.sensorsWidget.sensors

    @QtCore.pyqtSlot()
    def onIvStarted(self):
        self.topTabWidget.setCurrentIndex(0)
        self.bottomTabWidget.setCurrentIndex(1) # switch to IV temperature

    @QtCore.pyqtSlot()
    def onItStarted(self):
        self.topTabWidget.setCurrentIndex(1)
        self.bottomTabWidget.setCurrentIndex(2) # switch to It temperature

    @QtCore.pyqtSlot(object)
    def onMeasIvReading(self, reading):
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get('channels')[sensor.index].get('I')
                sensor.temperature = reading.get('channels')[sensor.index].get('temp')
        self.sensorsWidget.dataChanged() # HACK keep updated
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
        self.sensorsWidget.dataChanged() # HACK keep updated
        self.itTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.itSourceChart.append(reading)
        self.itChart.append(reading)

    @QtCore.pyqtSlot(object)
    def onSmuReading(self, reading):
        self.statusWidget.setVoltage(reading.get('U'))
        self.statusWidget.setCurrent(reading.get('I'))

    @QtCore.pyqtSlot()
    def onHalted(self):
        self.controlsWidget.onHalted()
        self.statusWidget.setCurrent(None)
        self.statusWidget.setVoltage(None)
        self.statusWidget.setCurrent(None)
        self.sensors().setEditable(True)