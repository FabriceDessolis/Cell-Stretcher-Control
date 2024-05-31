import sys
from PyQt5.QtWidgets import QApplication
from model import Model
from presenter import Presenter

def main():
    app = QApplication(sys.argv)
    
    from mainwindow import MainWindow
    view = MainWindow()
    model = Model()
    Presenter(view, model)

    view.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()