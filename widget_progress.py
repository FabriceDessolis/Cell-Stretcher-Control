import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal
from ressources.progress import Ui_Form


class ProgressWidget(QWidget, Ui_Form):
    
    def __init__(self):
        super(ProgressWidget, self).__init__()
        self.setupUi(self)


