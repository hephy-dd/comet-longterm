"""Longterm current measurement."""

import sys, os

os.environ['PYVISA_LIBRARY'] = '@py'

import comet
from .dashboard import DashboardWidget

ApplicationName = 'Longterm It'

class MainWindow(comet.MainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(ApplicationName)
        dashboard = DashboardWidget(self)
        self.setCentralWidget(dashboard)

def main():
    app = comet.Application()
    app.setName(ApplicationName)
    app.addWindow(MainWindow())
    return app.run()

if __name__ == '__main__':
    sys.exit(main())
