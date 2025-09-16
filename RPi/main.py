import sys
from PyQt5.QtWidgets import QApplication
from model import Model
from presenter import Presenter
import numpy
import pyqtgraph

def main():
    app = QApplication(sys.argv)

    from mainwindow import MainWindow
    view = MainWindow()
    model = Model()
    Presenter(view, model)

    view.show()
    app.exec()
    model.task_manager.ESP._disconnect()

if __name__ == '__main__':
    main()