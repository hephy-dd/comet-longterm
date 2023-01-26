import argparse
import logging
import os
import signal
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from . import __version__
from .controller import Controller

logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", dest="verbose", action="store_true", help="show verbose information")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def create_loggers(level):
    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s::%(name)s::%(levelname)s::%(message)s", "%Y-%m-%dT%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def main():
    args = parse_args()

    # Set logging level
    level = logging.DEBUG if args.verbose else logging.INFO
    create_loggers(level)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("comet-longterm")
    app.setApplicationVersion(__version__)
    app.setApplicationDisplayName(f"Longterm It {__version__}")
    app.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "assets", "icons", "longterm.ico")))
    app.setOrganizationName("HEPHY")
    app.setOrganizationDomain("hephy.at")

    # Register interupt signal handler
    def signal_handler(signum, frame):
        if signum == signal.SIGINT:
            app.quit()

    signal.signal(signal.SIGINT, signal_handler)

    # Initialize settings
    QtCore.QSettings()

    # Interrupt timer
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)

    # Controller
    controller = Controller()
    controller.loadSettings()
    controller.setLevel(level)

    logger.info("Longterm It version %s", __version__)
    app.exec()
    controller.storeSettings()


if __name__ == "__main__":
    main()
