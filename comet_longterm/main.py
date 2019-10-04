import sys

from PyQt5 import QtWidgets

from .centralwidget import CentralWidget
from comet import Application, MainWindow

def main():
    app = Application()
    app.setApplicationName('comet-longterm')

    w = MainWindow()
    w.resize(1280, 700)
    w.setCentralWidget(CentralWidget())
    w.show()

    return app.run()

if __name__ == '__main__':
    sys.exit(main())
