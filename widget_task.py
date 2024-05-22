import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import pyqtSignal
from ressources.task import Ui_Form


class TaskWidget(QWidget, Ui_Form):
    closeWidget = pyqtSignal(object)
    
    def __init__(self, task):
        super(TaskWidget, self).__init__()
        self.setupUi(self)

        self.mode = task.mode
        self.min_stretch = task.min_stretch
        self.max_stretch = task.max_stretch
        self.freq = task.freq
        self.ramp = task.ramp
        self.hold = task.hold
        self.duration = task.duration
        
        self.modes_pixmaps = {1: QPixmap("ressources/icons/ramp_s.svg"),
                              2: QPixmap("ressources/icons/cyclic_s.svg"),
                              3: QPixmap("ressources/icons/cyclic_ramp_s.svg"),
                              4: QPixmap("ressources/icons/hold_up_s.svg"),
                              5: QPixmap("ressources/icons/hold_down_s.svg")}

        self.set_image()
        self.set_settings()
        self.set_duration()
    
    def set_image(self):
        self.label_1.setPixmap(self.modes_pixmaps[self.mode])
        
    def set_settings(self):
        S = "S" + str(self.min_stretch) + "-" + str(self.max_stretch)
        settings = S
        if self.freq is not None:
            F = "F" + str(self.freq)
            settings += "\n"+F
        else:
            settings += "\n"
        if self.ramp is not None:
            R = "R" + str(self.ramp)
            settings += "\n"+R
        if self.hold is not None :
            H = "H" + str(self.hold)
            settings += "\n"+H
        if self.hold is None and self.ramp is None:
            settings += "\n"
        self.label_2.setText(settings)
        
    def set_duration(self):
        self.label_3.setText(self.duration[0] + self.duration[1] + "D\n" + self.duration[2] + self.duration[3] + "H\n" + self.duration[4] + self.duration[5] + "M")

    def is_selected(self, selected):
        if selected:
            self.frame.setStyleSheet("background-color: rgb(47,51,60);")
        else:
            self.frame.setStyleSheet("background-color: rgb(30,34,43);")