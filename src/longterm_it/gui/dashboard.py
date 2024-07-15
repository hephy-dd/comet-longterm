from typing import Optional

from PyQt5 import QtCore, QtWidgets, QtChart

from QCharted import ChartView

from .controlswidget import ControlsWidget
from .sensorswidget import SensorsWidget, SensorManager
from .statuswidget import StatusWidget
from .charts import IVChart, ItChart, CtsChart, IVTempChart, ItTempChart
from .charts import ShuntBoxChart, IVSourceChart, ItSourceChart

__all__ = ["DashboardWidget"]


class DashboardWidget(QtWidgets.QWidget):

    def __init__(self, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Longterm It")

        self.sensorsLabel = QtWidgets.QLabel(self)
        self.sensorsLabel.setText("Sensors")

        self.sensorsWidget = SensorsWidget(self)

        self.statusWidget = StatusWidget(self)

        self.controlsWidget = ControlsWidget(self)

        self.ivTab = QtWidgets.QWidget()
        self.ivChartView = ChartView()
        ivTabLayout = QtWidgets.QGridLayout(self.ivTab)
        ivTabLayout.addWidget(self.ivChartView, 0, 0, 1, 1)

        self.itTab = QtWidgets.QWidget()
        self.itChartView = ChartView()
        itTabLayout = QtWidgets.QGridLayout(self.itTab)
        itTabLayout.addWidget(self.itChartView, 0, 0, 1, 1)

        self.topTabWidget = QtWidgets.QTabWidget(self)
        self.topTabWidget.addTab(self.ivTab, "IV Curve")
        self.topTabWidget.addTab(self.itTab, "It Curve")
        self.topTabWidget.setCurrentIndex(0)

        self.ctsTab = QtWidgets.QWidget()
        self.ctsChartView = ChartView(self.ctsTab)
        ctsTabLayout = QtWidgets.QGridLayout(self.ctsTab)
        ctsTabLayout.addWidget(self.ctsChartView, 0, 0, 1, 1)

        self.ivTempTab = QtWidgets.QWidget()
        self.ivTempChartView = ChartView(self.ivTempTab)
        ivTempTabLayout = QtWidgets.QGridLayout(self.ivTempTab)
        ivTempTabLayout.addWidget(self.ivTempChartView, 0, 0, 1, 1)

        self.itTempTab = QtWidgets.QWidget()
        self.itTempChartView = ChartView(self.itTempTab)
        itTempTabLayout = QtWidgets.QGridLayout(self.itTempTab)
        itTempTabLayout.addWidget(self.itTempChartView, 0, 0, 1, 1)

        self.ivSourceTab = QtWidgets.QWidget()
        self.ivSourceChartView = ChartView(self.ivSourceTab)
        ivSourceTabLayout = QtWidgets.QGridLayout(self.ivSourceTab)
        ivSourceTabLayout.addWidget(self.ivSourceChartView, 0, 0, 1, 1)

        self.itSourceTab = QtWidgets.QWidget()
        self.itSourceChartView = ChartView(self.itSourceTab)
        itSourceTabLayout = QtWidgets.QGridLayout(self.itSourceTab)
        itSourceTabLayout.addWidget(self.itSourceChartView, 0, 0, 1, 1)

        self.shuntBoxTab = QtWidgets.QWidget()
        self.shuntBoxChartView = ChartView(self.shuntBoxTab)
        shuntBoxTabLayout = QtWidgets.QGridLayout(self.shuntBoxTab)
        shuntBoxTabLayout.addWidget(self.shuntBoxChartView, 0, 0, 1, 1)

        self.bottomTabWidget = QtWidgets.QTabWidget(self)
        self.bottomTabWidget.addTab(self.ctsTab, "Chamber")
        self.bottomTabWidget.addTab(self.ivTempTab, "IV Temp.")
        self.bottomTabWidget.addTab(self.itTempTab, "It Temp.")
        self.bottomTabWidget.addTab(self.ivSourceTab, "IV SMU")
        self.bottomTabWidget.addTab(self.itSourceTab, "It SMU")
        self.bottomTabWidget.addTab(self.shuntBoxTab, "Shunt Box")
        self.bottomTabWidget.setCurrentIndex(0)

        self.leftVerticalWidget = QtWidgets.QWidget(self)

        self.leftVerticalLayout = QtWidgets.QVBoxLayout(self.leftVerticalWidget)
        self.leftVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.leftVerticalLayout.addWidget(self.sensorsLabel)
        self.leftVerticalLayout.addWidget(self.sensorsWidget)
        self.leftVerticalLayout.addWidget(self.statusWidget)
        self.leftVerticalLayout.addWidget(self.controlsWidget)
        self.leftVerticalLayout.addStretch()
        self.leftVerticalLayout.setStretch(0, 0)
        self.leftVerticalLayout.setStretch(1, 0)
        self.leftVerticalLayout.setStretch(2, 0)
        self.leftVerticalLayout.setStretch(3, 1)
        # self.leftVerticalLayout.setStretch(4, 10)

        self.rightVerticalWidget = QtWidgets.QWidget(self)

        self.rightVerticalLayout = QtWidgets.QVBoxLayout(self.rightVerticalWidget)
        self.rightVerticalLayout.setContentsMargins(0, 0, 0, 0)
        self.rightVerticalLayout.addWidget(self.topTabWidget)
        self.rightVerticalLayout.addWidget(self.bottomTabWidget)

        self.horizontalSplitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.horizontalSplitter.setChildrenCollapsible(False)
        self.horizontalSplitter.addWidget(self.leftVerticalWidget)
        self.horizontalSplitter.addWidget(self.rightVerticalWidget)
        self.horizontalSplitter.setSizes([400, 800])

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.horizontalSplitter)

        self.createCharts()

        self.statusWidget.clearVoltage()
        self.statusWidget.clearCurrent()
        # TODO implement measurement timer
        self.controlsWidget.itDurationSpinBox.setEnabled(False)

        self.controlsWidget.operatorComboBox.setDuplicatesEnabled(False)

    def createCharts(self) -> None:
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

        def ivRangeChanged(minimum: float, maximum: float) -> None:
            self.ivSourceChart.fit()
            self.ivSourceChart.axisX.setRange(minimum, maximum)
            self.ivTempChart.fit()

        self.ivChart.axisX.rangeChanged.connect(ivRangeChanged)

        def itRangeChanged(minimum: float, maximum: float) -> None:
            self.itTempChart.fit()
            self.itTempChart.axisX.setRange(minimum, maximum)
            self.itSourceChart.fit()
            self.itSourceChart.axisX.setRange(minimum, maximum)

        self.itChart.axisX.rangeChanged.connect(itRangeChanged)

    def readSettings(self) -> None:
        settings = QtCore.QSettings()
        settings.beginGroup("dashboard")
        state = settings.value("splitter/state", QtCore.QByteArray(), QtCore.QByteArray)
        settings.endGroup()

        if not state.isEmpty():
            self.horizontalSplitter.restoreState(state)

        self.sensorsWidget.readSettings()

    def writeSettings(self) -> None:
        settings = QtCore.QSettings()
        settings.beginGroup("dashboard")
        settings.setValue("splitter/state", self.horizontalSplitter.saveState())
        settings.endGroup()
        self.sensorsWidget.writeSettings()

    def sensors(self) -> SensorManager:
        """Returns sensors manager."""
        return self.sensorsWidget.sensors

    @QtCore.pyqtSlot()
    def onIvStarted(self) -> None:
        self.topTabWidget.setCurrentIndex(0)
        self.bottomTabWidget.setCurrentIndex(1)  # switch to IV temperature

    @QtCore.pyqtSlot()
    def onItStarted(self) -> None:
        self.topTabWidget.setCurrentIndex(1)
        self.bottomTabWidget.setCurrentIndex(2)  # switch to It temperature

    @QtCore.pyqtSlot(dict)
    def onMeasIvReading(self, reading: dict) -> None:
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get("channels", {})[sensor.index].get("I")
                sensor.temperature = reading.get("channels", {})[sensor.index].get("temp")
        self.sensorsWidget.dataChanged()  # HACK keep updated
        self.ivTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.ivSourceChart.append(reading)
        self.ivChart.append(reading)

    @QtCore.pyqtSlot(dict)
    def onMeasItReading(self, reading: dict) -> None:
        for sensor in self.sensors():
            if sensor.enabled:
                sensor.current = reading.get("channels", {})[sensor.index].get("I")
                sensor.temperature = reading.get("channels", {})[sensor.index].get("temp")
        self.sensorsWidget.dataChanged()  # HACK keep updated
        self.itTempChart.append(reading)
        self.shuntBoxChart.append(reading)
        self.itSourceChart.append(reading)
        self.itChart.append(reading)

    @QtCore.pyqtSlot(dict)
    def onSmuReading(self, reading: dict) -> None:
        voltage = reading.get("U")
        if voltage is None:
            self.statusWidget.clearVoltage()
        else:
            self.statusWidget.setVoltage(voltage)
        current = reading.get("I")
        if current is None:
            self.statusWidget.clearCurrent()
        else:
            self.statusWidget.setCurrent(current)

    @QtCore.pyqtSlot()
    def onHalted(self) -> None:
        self.controlsWidget.onHalted()
        self.statusWidget.clearCurrent()
        self.statusWidget.clearVoltage()
        self.statusWidget.clearCurrent()
        self.sensors().setEditable(True)
