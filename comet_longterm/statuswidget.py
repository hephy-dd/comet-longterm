from PyQt5 import QtCore, QtWidgets

from comet import UiLoaderMixin

class StatusWidget(QtWidgets.QWidget, UiLoaderMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loadUi()

if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = StatusWidget()
    w.show()
    app.exec_()
