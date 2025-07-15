from PyQt5.QtWidgets import QListWidgetItem
from PyQt5.QtCore import *

from methods import *
from task_manager import TaskManager
from pop_up_dialog import Dialog

class Model(QObject):
    """ This stores all the settings that were input in the mainwindow,
        and it creates and manages tasks objects """
    giveTaskToView = pyqtSignal(object, object)
    removeTaskFromView = pyqtSignal(object)
    progressBarUpdate = pyqtSignal(float, float)
    timesUpdate = pyqtSignal(tuple)
    startNextTask = pyqtSignal(int)
    runStarted = pyqtSignal(dict)
    allTaskEnded = pyqtSignal()

    def __init__(self):
        super(Model, self).__init__()
        self.tasks = [] # [[item, task object], [...]]
        self.task_manager = TaskManager() # will be used to hold the TaskManager object
        self.task_manager.connect_to_arduino()
        self.task_manager.progressBarUpdate.connect(lambda task, total: self.progressBarUpdate.emit(task, total))
        self.task_manager.startNextTask.connect(lambda index: self.startNextTask.emit(index))
        self.task_manager.timesUpdate.connect(lambda times: self.timesUpdate.emit(times))
        self.task_manager.allTaskEnded.connect(self.end)

        self.current_mode = 1
        self.current_button = 1

        self.run_state = {"running": False,
                          "paused": False}

        self.modes = {1: "RAMP",
                      2: "CYCLIC",
                      3: "CYCLIC_RAMP",
                      4: "HOLD_UP",
                      5: "HOLD_DOWN"}

        # List all the push-buttons that open the keypad
        self.settings_buttons = {"not_duration": [11, 12, 21, 22, 23, 31, 32, 33, 34, 41, 42, 43, 44, 51, 52, 53, 54],
                                 "duration": [15, 25, 35, 45, 55],
                                 "stepper": [60, 61]}

        # Dictionary to associate button settings with values, looks like {11: None, 12: 2.0, 13: None, etc}
        self.settings_values = {}

    def add_new_task(self):
        # create empty dict
        settings = {"mode": None,
                    "min_stretch": None,
                    "max_stretch": None,
                    "freq": None,
                    "ramp": None,
                    "hold": None,
                    "duration": None}

        # check if all values were added
        for button, value in self.settings_values.items():
            if int(button/10) == self.current_mode:
                if value is None:
                    Dialog("Please input all settings first")
                    return

        # if so, create variables holding these values
                else:
                    setting = button % 10
                    settings["mode"] = self.current_mode
                    if setting == 1:
                        settings["min_stretch"] = value
                    elif setting == 2:
                        settings["max_stretch"] = value
                    elif setting == 3:
                        settings["freq"] = value
                    elif setting == 4:
                        if self.current_mode == 3:
                            settings["ramp"] = value
                        else:
                            settings["hold"] = value
                    elif setting == 5:
                        settings["duration"] = value

        # change nonetype values to 0
        for key, value in settings.items():
            if value is None:
                settings[key] = 0
                
        # check for inconsistencies
        if settings["min_stretch"] == settings["max_stretch"]:
            Dialog("min stretch equals max stretch, so no stretch")
            return
        if settings["min_stretch"] > settings["max_stretch"]:
            Dialog("Please set max stretch higher than min stretch")
            return
        if settings["freq"] == 0 and settings["mode"] != 1:
            Dialog("We need some frequency")
            return
        if settings["freq"] > 2:
            Dialog("Frequency too high, please don't try to break the stretcher")
            return

        # then ask task manager to create an object with those values
        self.create_task_object(settings)

    def create_task_object(self, settings: dict):
        # add the visual widget containing the task settings
        item = QListWidgetItem()
        task = Task(settings)
        self.tasks.append([item, task])

        self.giveTaskToView.emit(item, task)

    def duplicate_task(self, item):
        for tasklist in self.tasks:
            if item == tasklist[0]:                           # if we find the same item in the tasks list
                task = tasklist[1]                               # we extract the task object
                self.create_task_object(task.settings)        # we duplicate the settings and create a new task

    def remove_task(self, item):
        for tasklist in self.tasks:
            if item == tasklist[0]:                              # if we found the same item in the tasks list
                self.tasks.remove(tasklist)
                self.removeTaskFromView.emit(item)

    def organize_tasks(self, items_order: list):
        provisional_tasklist = []
        for i in items_order:
            for j in self.tasks:
                if i == j[0]:
                    provisional_tasklist.append(j)
                    self.tasks.remove(j)
        self.tasks = provisional_tasklist

    def start(self, items_order: list):
        # rearrange tasks in the right order
        self.organize_tasks(items_order)

        # pop up a window with a review of all the tasks to be done and the total time it will take
        # but first, create a task list without the items in self.tasks
        tasks = []
        for i in self.tasks:
            tasks.append(i[1])
        days, hours, minutes = calculate_duration(tasks)
        accepted = Dialog("Confirm start operation ?\nTotal time : %s days %s hours %s minutes" % (days, hours, minutes), True).result
        # send to a task manager that will count time and send tasks to arduino when they are ready
        if accepted:
            self.task_manager.init(tasks)
            self.run_state["running"] = True
            self.runStarted.emit(self.run_state)
            return 1
        else:
            return 0
        
    def end(self):
        self.run_state["running"] = False
        self.run_state["paused"] = False
        self.allTaskEnded.emit()
        

    def stepper_togo_changed(self):
        # When applying a value (mm or %), affect the other one
        # 1mm = 10% for a l0 of 10mm
        val = self.settings_values[self.current_button]
        if self.current_button == 60:
            affected_val = val * 10
        elif self.current_button == 61:
            affected_val = val / 10
            if type(affected_val) is float:
                if affected_val.is_integer():
                    affected_val = int(affected_val)

        for button in self.settings_buttons["stepper"]:
            if button != self.current_button:
                affected_button = button

        self.settings_values[affected_button] = affected_val

        return affected_button, affected_val

    def stepper_go(self):
        if self.run_state["running"] is True and self.run_state["paused"] is False:
            Dialog("A process is currently running, please pause it first to move manually")
            return
        if self.settings_values[60] is None:
            Dialog("Enter distance to go first")
            return
        # go somewhere

    def send_to_arduino(self):
        ...


class Task:
    """
    Object that holds task settings, it comes from the task manager as a dictionary
    """
    def __init__(self, settings):
        self.settings = settings
        self.mode = settings["mode"]
        self.min_stretch = settings["min_stretch"]
        self.max_stretch = settings["max_stretch"]
        self.freq = settings["freq"]
        self.ramp = settings["ramp"]
        self.hold = settings["hold"]
        self.duration = settings["duration"]
