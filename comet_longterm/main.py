"""Longterm current measurement."""

import sys

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

    # Setup default devices
    settings = comet.Settings()
    devices = settings.devices()
    if 'cts' not in devices:
        settings.setDevice('cts', 'TCPIP::192.168.100.205::1080::SOCKET')
    if 'smu' not in devices:
        settings.setDevice('smu', 'TCPIP::10.0.0.3::10002::SOCKET')
    if 'multi' not in devices:
        settings.setDevice('multi', 'TCPIP::10.0.0.3::10001::SOCKET')

    window = MainWindow()
    window.show()

    return app.run()

if __name__ == '__main__':
    sys.exit(main())
