import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
from ressources.view import Ui_MainWindow
from widget_numberpad import NumberPad
from widget_task import TaskWidget
from pop_up_dialog import Dialog

class Styles(object):
    
    SELECTED = "QPushButton { background-color: rgb(47,51,60) } "
    NOT_SELECTED = "QPushButton { background-color: rgb(30,34,43) } "
    
class Icons(object):
    """
    1 : RAMP, 2 : CYCLIC, 3 : CYCLIC RAMP, 4 : HOLD UP, 5 : HOLD DOWN
    """

    SELECTED = {1: QIcon("ressources/icons/ramp_s.svg"),
                2: QIcon("ressources/icons/cyclic_s.svg"),
                3: QIcon("ressources/icons/cyclic_ramp_s.svg"),
                4: QIcon("ressources/icons/hold_up_s.svg"),
                5: QIcon("ressources/icons/hold_down_s.svg"),
               }
    
    NOT_SELECTED = {1: QIcon("ressources/icons/ramp.svg"),
                    2: QIcon("ressources/icons/cyclic.svg"),
                    3: QIcon("ressources/icons/cyclic_ramp.svg"),
                    4: QIcon("ressources/icons/hold_up.svg"),
                    5: QIcon("ressources/icons/hold_down.svg"),
                   }
    
    SMALL = QSize(50, 50)
    BIG = QSize(60, 60)
    

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, obj=None, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)
        self.setupUi(self)

        self.pad = NumberPad()
        self.pad.setWindowModality(Qt.ApplicationModal)
        self.pad.closeWidget.connect(self.hide_numberpad)

        self.listWidget = ListWidget()
        self.setup_list_widget()
        self.listWidget.itemPressed.connect(lambda item: self.item_selected(item))

        self.pushButton_3.clicked.connect(self.tests)

    def tests(self):
        a = self.listWidget.count()
        print(a)

    def setup_list_widget(self):
        # this is a workaround for a pyqt bug deleting items when being dragged
        self.gridLayout_list = QGridLayout(self.frame_list)
        self.gridLayout_list.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_list.setHorizontalSpacing(6)
        self.gridLayout_list.setVerticalSpacing(6)
        self.listWidget.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        self.listWidget.setItemAlignment(Qt.AlignCenter)
        self.gridLayout_list.addWidget(self.listWidget)
        self.listWidget.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.listWidget.setDragEnabled(True)
        self.listWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.listWidget.setDefaultDropAction(Qt.MoveAction)
        self.listWidget.setMovement(QListView.Snap)
        self.listWidget.setViewMode(QListView.ListMode)
        self.listWidget.setObjectName("listWidget")

    def mode_changed(self, number):
        # Do graphic stuff
        getattr(self, f"pushButton_m{number}").setStyleSheet(Styles.SELECTED) # change background
        getattr(self, f"pushButton_m{number}").setIcon(Icons.SELECTED[number]) # make it neon effect
        getattr(self, f"pushButton_m{number}").setIconSize(Icons.BIG) # change icon size
        for i in range(1, 6):
            if i is not number:
                getattr(self, f"pushButton_m{i}").setStyleSheet(Styles.NOT_SELECTED) # change background
                getattr(self, f"pushButton_m{i}").setIcon(Icons.NOT_SELECTED[i]) # make it NOT neon effect
                getattr(self, f"pushButton_m{i}").setIconSize(Icons.SMALL) # change icon size
                
        # Change corresponding settings tab
        self.stackedWidget.setCurrentIndex(number - 1)

    def display_value(self, value, current_button):
        if self.pad._type == "not_duration":
            getattr(self, f"pushButton_{current_button}").setText(str(value))
        if self.pad._type == "duration":
            getattr(self, f"pushButton_{current_button}").setText(value[0]+value[1]+"D "
                                                                 +value[2]+value[3]+"H "
                                                                 +value[4]+value[5]+"MN")

    @pyqtSlot()
    def create_task(self, item: object, task: object):

        t = TaskWidget(task)
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, t)

        item.setSizeHint(t.sizeHint())
        item.setTextAlignment(Qt.AlignCenter) # MARCHE PAS

    @pyqtSlot()
    def remove_task(self, item: object):
        row = self.listWidget.row(item)
        self.listWidget.takeItem(row)
        self.listWidget.removeItemWidget(item)

    def item_selected(self, item_selected):
        """
        change the background color to outline the selected item
        """
        self.listWidget.itemWidget(item_selected).is_selected(True)
        # then return to initial color for all the rest
        for i in range(self.listWidget.count()):
            not_selected = self.listWidget.item(i)
            if not_selected != item_selected:
                self.listWidget.itemWidget(not_selected).is_selected(False)

    def show_numberpad(self):
        self.pad.show()
        self.pad.move(self.pos() + QPoint(200, 70))

    def hide_numberpad(self):
        self.pad.hide()

"""
    def closeEvent(self):
        sys.exit(0)
"""

class ListWidget(QListWidget):
    # this is a workaround for a pyqt bug deleting items when being dragged
    def dragMoveEvent(self, event):
        if ((target := self.row(self.itemAt(event.pos()))) ==
            (current := self.currentRow()) + 1 or
            (current == self.count() - 1 and target == -1)):
            event.ignore()
        else:
            super().dragMoveEvent(event)
