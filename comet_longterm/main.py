"""Longterm current measurement."""

import sys, os

os.environ['PYVISA_LIBRARY'] = '@py'

import comet
from .dashboard import DashboardWidget

class MainWindow(comet.MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        dashboard = DashboardWidget(self)
        self.setCentralWidget(dashboard)
        self.setWindowTitle(dashboard.windowTitle())

def main():
    app = comet.Application()
    app.setName('LongtermIt')
    app.addWindow(MainWindow())
    return app.run()

if __name__ == '__main__':
    sys.exit(main())
