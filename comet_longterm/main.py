import logging
import sys

from PyQt5 import QtWidgets

from .centralwidget import CentralWidget
from comet import Application, MainWindow
from . import __version__

def main():
    app = Application()
    app.setApplicationName('comet-longterm')

    w = MainWindow()
    w.resize(1280, 700)
    w.setCentralWidget(CentralWidget(w))
    w.setWindowTitle("{} {}".format(w.windowTitle(), __version__))
    w.show()

    return app.run()

if __name__ == '__main__':
    sys.exit(main())
