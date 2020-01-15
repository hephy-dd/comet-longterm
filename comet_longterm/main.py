import argparse
import logging
import sys

from PyQt5 import QtWidgets

from .centralwidget import CentralWidget
from comet import Application, MainWindow
from . import __version__

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', dest='verbose', action='store_true', help="show verbose information")
    return parser.parse_args()

def main():
    app = Application()
    app.setApplicationName('comet-longterm')

    args = parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    w = MainWindow()
    w.resize(1280, 700)
    w.setCentralWidget(CentralWidget(w))
    w.setWindowTitle("{} {}".format(w.windowTitle(), __version__))
    w.show()

    return app.run()

if __name__ == '__main__':
    sys.exit(main())
