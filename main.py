import sys
from PyQt5.QtWidgets import QApplication
import qdarktheme
from model import Model
from presenter import Presenter

def main():
    app = QApplication(sys.argv)
    #qdarktheme.setup_theme()
    
    from mainwindow import MainWindow
    view = MainWindow()
    manager = Model()
    Presenter(view, manager)

    view.show()
    sys.exit(app.exec())

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
