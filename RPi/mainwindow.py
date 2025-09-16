import sys
import os
#import sip
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
from ressources.view import Ui_MainWindow
from widget_numberpad import NumberPad
from widget_task import TaskWidget
from widget_monitoring import MonitoringWidget
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
        self.tasks = [] # Not organized when drag and dropping widgets

        self.pad = NumberPad()
        self.pad.setWindowModality(Qt.ApplicationModal)
        self.pad.setWindowFlag(Qt.FramelessWindowHint)
        self.pad.closeWidget.connect(self.hide_numberpad)

        self.monitoring = MonitoringWidget(parent=self.frame_monitoring)
        self.frame_monitoring.setLayout(self.gridLayout_monitoring)
        
        self.listWidget = ListWidget()
        self.setup_list_widget()
        self.listWidget.itemPressed.connect(lambda item: self.item_selected(item))
        
        self.frame_taskprogress.hide()

        self.pushButton_3.clicked.connect(self.tests)

    def tests(self):
        print(self.tasks)

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
        if self.pad._type == "stepper":
            getattr(self, f"pushButton_{current_button}").setText(str(value))

    @pyqtSlot()
    def create_task(self, item: object, task: object):
        t = TaskWidget(task)
        self.tasks.append(t)
        self.listWidget.addItem(item)
        self.listWidget.setItemWidget(item, t)

        item.setSizeHint(t.sizeHint())
        item.setTextAlignment(Qt.AlignCenter) # MARCHE PAS
        

    @pyqtSlot()
    def remove_task(self, item: object):
        # First find the widget in the tasks list and remove it
        widget = self.listWidget.itemWidget(item)
        self.tasks.remove(widget)
        
        # Then remove it from the listwidget
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
                
    def create_taskrecap_view(self, items):
        """
        Start button was pressed and accepted
        Add widgets to the RUN tab as visual information on the tasks order
        """
        # First remove everything in the taskrecap frame
        self.clean_taskrecap_view()
        # Then add the progress task widgets
        first_item = True
        for i in items:
            # pick the widget from the itemwidget
            widget = self.listWidget.itemWidget(i)
            # create a progressTaskWidget
            w = ProgressTaskWidget(widget)
            if first_item:
                w.set_current_task(True)           # change label to "current task"
                first_item = False
            self.horizontalLayout_27.insertWidget(-1, w)

        # Show one or two progress bars
        if len(items) == 1:
            self.frame_taskprogress.hide()
        else:
            self.frame_taskprogress.show()

        # Finally, swap to tab RUN
        self.tabWidget.setCurrentIndex(1)

    def clean_taskrecap_view(self):
        count = self.horizontalLayout_27.count()
        while count > 0: # while count > 0
            item_to_remove = self.horizontalLayout_27.itemAt(0)
            widget_to_remove = item_to_remove.widget()
            self.horizontalLayout_27.removeWidget(widget_to_remove)
            widget_to_remove.deleteLater()
            count -= 1

    def start_pause_abort(self, run_state):
        if run_state["running"] is True:
            if run_state["paused"] is True:
                text = "RESUME"
            else:
                text = "PAUSE"
        else:
            text = "START"
        self.pushButton_start.setText(text)

    def start_next_task(self, index):
        count = self.horizontalLayout_27.count()
        while count > 0:
            w = self.horizontalLayout_27.itemAt(count - 1).widget()
            if index == (count - 1):
                w.set_current_task(True)
            else:
                w.set_current_task(False)
            count -= 1

    def update_progress_bar(self, taskvalue, totalvalue):
        self.progressBar_task.setValue(int(taskvalue))
        self.progressBar_total.setValue(int(totalvalue))

    def update_times(self, times):
        # comes as (("","",""), ("","",""), ("","",""), ("","",""))
        i = 1
        for val in times:
            text = val[0] + "D " + val[1] + "H " + val[2] + "MN"
            if getattr(self, f"label_t{i}").text() != text:
                getattr(self, f"label_t{i}").setText(text)
            i += 1

    def clean_after_abort(self):
        self.update_progress_bar(0, 0)
        self.update_times((("00", "00", "00"), ("00", "00", "00"), ("00", "00", "00"), ("00", "00", "00")))
        self.frame_taskprogress.hide()
        self.clean_taskrecap_view()

    def show_numberpad(self):
        self.pad.show()
        self.pad.move(self.pos() + QPoint(200, 50))

    def hide_numberpad(self):
        self.pad.hide()

    def update_stepper_position(self, position):
        # Position is a string of the step position

        self.label_pos_mm.setText()
        self.label_pos_percent.setText()
        self.label_pos_steps.setText(position)
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
            
    
class ProgressTaskWidget(QWidget):
    """
    Reusable custom widget that uses widget_task.TaskWidget and adds a label on top
    Used to recap the selected tasks and to inform on the one runing 
    """
    
    def __init__(self, widget, isFirst=False):
        super(ProgressTaskWidget, self).__init__()

        # Create a task widget with the same imported settings
        self.task = TaskWidget(widget.settings)

        self.verticalLayout = QVBoxLayout()
        self.verticalSpacer = QSpacerItem(20, 56, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.verticalSpacer2 = QSpacerItem(20, 56, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignCenter)
        
        self.verticalLayout.addItem(self.verticalSpacer)
        self.verticalLayout.addWidget(self.label)
        self.verticalLayout.addWidget(self.task)
        self.verticalLayout.addItem(self.verticalSpacer2)

        self.setLayout(self.verticalLayout)
        
        if isFirst:
            self.set_current_task(True)
            
    def set_current_task(self, iscurrent):
        if iscurrent:
            self.label.setText("Current task")
        else:
            self.label.setText("")