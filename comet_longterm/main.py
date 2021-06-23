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
    parser.add_argument('--version', action='version', version=f"%(prog)s {__version__}")
    return parser.parse_args()

def main():
    args = parse_args()

    # Set logging level
    level = logging.DEBUG if args.verbose else logging.INFO
    logging.getLogger().setLevel(level)
    logging.info("Longterm It version %s", __version__)

    app = Application()
    app.setApplicationName('comet-longterm')

    window = MainWindow()
    window.setCentralWidget(CentralWidget(window))
    window.setWindowTitle("{} {}".format(window.windowTitle(), __version__))
    window.centralWidget().setLevel(level)
    window.resize(1280, 700)
    window.show()

    return app.run()

if __name__ == '__main__':
    sys.exit(main())
