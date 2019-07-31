import sys

from PyQt5 import QtCore, QtWidgets

from comet.qt import MainWindow

def main():
    app = QtWidgets.QApplication(sys.argv)

    app.setOrganizationName('HEPHY')
    app.setOrganizationDomain('hephy.at');
    app.setApplicationName('CometLongterm');

    QtCore.QSettings()

    w = MainWindow()
    w.show()

    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)

    app.exec_()

if __name__ == '__main__':
    sys.exit(main())
