import time
import threading
import sys, os
import signal

os.environ['PYVISA_LIBRARY'] = '@py'

from comet.widgets import Application

from .dashboard import DashboardWidget

class Application(Application):

    name = "Longterm It"

    def createCentralWidget(self, context):
        return DashboardWidget(context)

def main():
    app = Application()
    return app.run()

if __name__ == '__main__':
    sys.exit(main())
