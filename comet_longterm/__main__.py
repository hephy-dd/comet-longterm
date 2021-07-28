import argparse
import logging
import signal
import sys

from PyQt5 import QtCore
from PyQt5 import QtWidgets

from . import __version__
from .controller import Controller
from comet.ui import Application

logger = logging.getLogger(__name__)

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

    app = Application()
    app.qt.setApplicationName("comet-longterm")
    app.qt.setApplicationVersion(__version__)
    app.qt.setApplicationDisplayName(f"Longterm It {__version__}")
    app.qt.setOrganizationName("HEPHY")
    app.qt.setOrganizationDomain("hephy.at")

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
    result = app.qt.exec()
    controller.storeSettings()

    return result

if __name__ == '__main__':
    sys.exit(main())
