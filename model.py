from PyQt5.QtWidgets import QListWidgetItem

from arduino import Arduino
from PyQt5.QtCore import pyqtSignal, QObject
from pop_up_dialog import Dialog

class Model(QObject):
    """ This stores all the settings that were input in the mainwindow,
        and it creates and manages tasks objects """
    giveTaskToView = pyqtSignal(object, object)
    removeTaskFromView = pyqtSignal(object)

    def __init__(self):
        super(Model, self).__init__()
        self.tasks = [] # [[item, task object], [...]]

        self.current_mode = 1
        self.current_button = 1

        self.modes = {1: "RAMP",
                      2: "CYCLIC",
                      3: "CYCLIC_RAMP",
                      4: "HOLD_UP",
                      5: "HOLD_DOWN"}

        # List all the push-buttons that open the keypad
        self.settings_buttons = {"not_duration": [11, 12, 21, 22, 23, 31, 32, 33, 34, 41, 42, 43, 44, 51, 52, 53, 54],
                                 "duration": [15, 25, 35, 45, 55]}

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

    def start(self, items_order: list):
        # rearrange tasks in the right order
        provisional_tasklist = []
        for i in items_order:
            for j in self.tasks:
                if i == j[0]:
                    provisional_tasklist.append(j)
                    self.tasks.remove(j)
        self.tasks = provisional_tasklist

        # pop up a window with a review of all the tasks to be done and the total time it will take
        days, hours, minutes = self.calculate_total_duration()
        acceptwindow = Dialog("Confirm start operation ?\nTotal time : %s days %s hours %s minutes" % (days, hours, minutes), True).result

        # send to a task manager that will count time and send tasks to arduino when they are ready
        if acceptwindow:
            task_list = []
            for i in self.tasks:
                task_list.append(i[1])
            TaskManager(task_list)

    def calculate_total_duration(self):
        durations = [0, 0, 0] # days, hours, minutes
        for i in self.tasks:
            obj = i[1]
            durations[0] = durations[0] + int(obj.duration[0:2]) # days
            durations[1] = durations[1] + int(obj.duration[2:4]) # hours
            durations[2] = durations[2] + int(obj.duration[4:6]) # minutes

        minutes, hours = durations[2]%60, durations[2]//60
        hours, days = durations[1]%24 + hours, durations[1]//24
        days = durations[0] + days

        return days, hours, minutes

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


class TaskManager:

    def __init__(self, task_list):
        self.tasks = task_list # collection of Task objects
        print(self.tasks)