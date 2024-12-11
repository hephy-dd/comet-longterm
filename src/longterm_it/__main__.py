import argparse
import logging
import os
import signal
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from . import __version__
from .controller import Controller
from .gui.mainwindow import MainWindow

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", dest="verbose", action="store_true", help="show verbose information")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args()


def create_loggers(level) -> None:
    logger = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s::%(name)s::%(levelname)s::%(message)s", "%Y-%m-%dT%H:%M:%S")
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(level)


def main() -> None:
    args = parse_args()

    # Set logging level
    level = logging.DEBUG if args.verbose else logging.INFO
    create_loggers(level)

    logger.info("Longterm It version %s", __version__)

    # Set the locale to EN-US
    locale = QtCore.QLocale(QtCore.QLocale.English, QtCore.QLocale.UnitedStates)
    QtCore.QLocale.setDefault(locale)

    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationName("comet-longterm")
    app.setApplicationVersion(__version__)
    app.setApplicationDisplayName(f"Longterm It {__version__}")
    app.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), "assets", "icons", "longterm.ico")))
    app.setOrganizationName("HEPHY")
    app.setOrganizationDomain("hephy.at")

    # Register interupt signal handler
    def signal_handler(signum, frame):
        app.quit()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Interrupt timer
    timer = QtCore.QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)

    # Controller
    window = MainWindow()
    window.setProperty("contentsUrl", "https://github.com/hephy-dd/comet-longterm")
    window.setProperty("aboutText",
        f"""<h3>Longterm It</h3>
        <p>Version {__version__}</p>
        <p>Long term sensor It measurements in CTS climate chamber.</p>
        <p>&copy; 2019-2024 hephy.at</p>""",
    )
    window.logWindow.addLogger(logging.getLogger())
    window.logWindow.setLevel(level)
    controller = Controller(window)
    controller.readSettings()
    window.show()

    import time, random
    def work():
        time.sleep(8)
        for i in range (16*1024):
            r = i + random.random()
            f = random.choice(["https://github.com/hephy-dd/comet-longterm", "&copy; 2019-2024 hephy.at", "fun with princess Lavi ^_^"])
            logging.info(f"[{r}]Long term sensor It measurements in CTS climate foo bar baz sadhf ajkfhsajkfh dsafhsajkfhsafjk asfjsajkfsakfsdaf {f}")
            time.sleep(random.uniform(0.00001, 0.0001))
        logging.info("~~~~~DONE~~~~~")

    import threading
    t = threading.Thread(target=work, daemon=True)
    t.start()

    app.aboutToQuit.connect(controller.writeSettings)
    app.exec()


if __name__ == "__main__":
    main()
