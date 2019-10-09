from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

class StatusWidget(QtWidgets.QWidget, UiLoaderMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()

    def setVoltage(self, voltage):
        self.ui.voltageLineEdit.setText("{:.3f} V".format(voltage))

    def setCurrent(self, current):
        self.ui.currentLineEdit.setText("{:.3f} V".format(current))

    def setTemperature(self, temperature):
        self.ui.tempLineEdit.setText("{:.1f} °C".format(temperature))

    def setHumidity(self, humidity):
        self.ui.humidLineEdit.setText("{:.1f} %rH".format(humidity))

    def setProgram(self, program):
        if program == 0:
            self.ui.programLineEdit.setText(self.tr("halted"))
        else:
            self.ui.programLineEdit.setText(self.tr("P{}").format(program))

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = StatusWidget()
    w.setVoltage(42)
    w.setCurrent(.42)
    w.setTemperature(4.2)
    w.setHumidity(2.4)
    w.setProgram(0)
    w.show()
    app.exec_()
