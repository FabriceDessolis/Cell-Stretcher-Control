from PyQt5.QtWidgets import QListWidgetItem

from arduino import Arduino
from PyQt5.QtCore import *
from pop_up_dialog import Dialog

class Model(QObject):
    """ This stores all the settings that were input in the mainwindow,
        and it creates and manages tasks objects """
    giveTaskToView = pyqtSignal(object, object)
    removeTaskFromView = pyqtSignal(object)
    progressBarUpdate = pyqtSignal(float)

    def __init__(self):
        super(Model, self).__init__()
        self.tasks = [] # [[item, task object], [...]]
        self.task_manager = None # will be used to hold the TaskManager object

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
        print("ACCEPT WINDOW :", acceptwindow)
        # send to a task manager that will count time and send tasks to arduino when they are ready
        if acceptwindow:
            task_list = []
            for i in self.tasks:
                task_list.append(i[1])
            self.task_manager = TaskManager(task_list)
            self.task_manager.progressBarUpdate.connect(lambda value: self.progressBarUpdate.emit(value))
        else:
            return

    def calculate_total_duration(self):
        durations = [0, 0, 0]  # days, hours, minutes
        for i in self.tasks:
            obj = i[1]
            durations[0] = durations[0] + int(obj.duration[0:2])  # days
            durations[1] = durations[1] + int(obj.duration[2:4])  # hours
            durations[2] = durations[2] + int(obj.duration[4:6])  # minutes

        minutes, hours = durations[2] % 60, durations[2] // 60
        hours, days = durations[1] % 24 + hours, durations[1] // 24
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


class TaskManager(QObject):
    qtimer_timeout = 1000 # 1s
    progressBarUpdate = pyqtSignal(float)

    def __init__(self, task_list):
        super(TaskManager, self).__init__()
        self.tasks = task_list # collection of Task objects
        self.running_task = 0 # for index
        self.task_end_time = 0
        self.task_duration = 0
        self.task_percent_done = 0
        self.run_task()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_remaining_time)
        self.timer.start(self.qtimer_timeout)

    def run_task(self):
        # Get the epoch where we started
        start_time = QDateTime.currentSecsSinceEpoch()
        self.task_duration = self.get_task_duration()
        self.task_end_time = start_time + self.task_duration

    def check_remaining_time(self):
        remaining_time = self.task_end_time - QDateTime.currentSecsSinceEpoch()
        # update QProgressBar
        new_task_percent_done = 100 - ((remaining_time / self.task_duration) * 100)
        if new_task_percent_done - self.task_percent_done >= 1:
            self.task_percent_done = new_task_percent_done
            self.progressBarUpdate.emit(self.task_percent_done) # goes to Model
        # check if task has ended
        if remaining_time < (self.qtimer_timeout / 1000) or remaining_time < 0:   # DONT FORGET TO CHANGE
            self.task_ended()

    def task_ended(self):
        # Do some arduino things
        # Check if there are other tasks, if so, change task
        if len(self.tasks) > (self.running_task + 1):
            print("GO TO NEXT TASK")
            self.running_task += 1
            self.run_task()
        else:
            # some signals to inform user
            print("ALL TASKS ENDED")
            self.timer.stop()
            return

    def get_task_duration(self):
        days, hours, minutes = self.calculate_task_duration(self.tasks[self.running_task])
        s_time = days*8.64e4 + hours*3.6e3 + minutes*60
        return s_time

    def calculate_task_duration(self, task):
        durations = [0, 0, 0]  # days, hours, minutes
        durations[0] = durations[0] + int(task.duration[0:2])  # days
        durations[1] = durations[1] + int(task.duration[2:4])  # hours
        durations[2] = durations[2] + int(task.duration[4:6])  # minutes

        minutes, hours = durations[2] % 60, durations[2] // 60
        hours, days = durations[1] % 24 + hours, durations[1] // 24
        days = durations[0] + days

        return days, hours, minutes


""" FUNCTIONS """


