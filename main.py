import sys
from PyQt5.QtWidgets import QApplication
import qdarktheme
from model import Model
from presenter import Presenter

def main():
    app = QApplication(sys.argv)
    
    from mainwindow import MainWindow
    view = MainWindow()
    manager = Model()
    Presenter(view, manager)

    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()