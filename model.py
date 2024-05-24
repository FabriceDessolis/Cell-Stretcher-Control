from PyQt5.QtWidgets import QListWidgetItem

from arduino import Arduino
from PyQt5.QtCore import *
from pop_up_dialog import Dialog

class Model(QObject):
    """ This stores all the settings that were input in the mainwindow,
        and it creates and manages tasks objects """
    giveTaskToView = pyqtSignal(object, object)
    removeTaskFromView = pyqtSignal(object)
    progressBarUpdate = pyqtSignal(float, float)
    startNextTask = pyqtSignal(int)

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
        # but first, create a task list without the items in self.tasks
        tasks = []
        for i in self.tasks:
            tasks.append(i[1])
        days, hours, minutes = calculate_duration(tasks)
        acceptwindow = Dialog("Confirm start operation ?\nTotal time : %s days %s hours %s minutes" % (days, hours, minutes), True).result
        print("ACCEPT WINDOW :", acceptwindow)
        # send to a task manager that will count time and send tasks to arduino when they are ready
        if acceptwindow:
            task_list = []
            for i in self.tasks:
                task_list.append(i[1])
            self.task_manager = TaskManager(task_list)
            self.task_manager.progressBarUpdate.connect(lambda task, total: self.progressBarUpdate.emit(task, total))
            self.task_manager.startNextTask.connect(lambda index: self.startNextTask.emit(index))
        else:
            return

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
    progressBarUpdate = pyqtSignal(float, float)
    startNextTask = pyqtSignal(int)

    def __init__(self, task_list):
        super(TaskManager, self).__init__()
        self.tasks = task_list # collection of Task objects
        self.running_task = 0 # for index

        self.task_end_time = 0 # epoch in seconds
        self.task_duration = 0 # seconds
        self.task_percent_done = 0

        self.total_end_time = 0 # seconds
        self.total_duration = 0 # seconds
        self.total_percent_done = 0

        self.get_total_duration()
        self.run_task()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_remaining_time)
        self.timer.start(self.qtimer_timeout)

    def get_total_duration(self):
        self.total_duration = calculate_duration(self.tasks, return_seconds=True)

    def run_task(self):
        self.task_percent_done = 0
        # Get the epoch where we started
        start_time = QDateTime.currentSecsSinceEpoch()
        self.task_duration = calculate_duration(self.tasks[self.running_task], return_seconds=True)
        self.task_end_time = start_time + self.task_duration
        if self.running_task == 0: # if first task
            self.total_end_time = start_time + self.total_duration

    def check_remaining_time(self):
        task_remaining_time = self.task_end_time - QDateTime.currentSecsSinceEpoch()
        total_remaining_time = self.total_end_time - QDateTime.currentSecsSinceEpoch()
        # update QProgressBar
        new_task_percent_done = 100 - ((task_remaining_time / self.task_duration) * 100)
        new_total_percent_done = 100 - ((total_remaining_time / self.total_duration) * 100)
        # here we only emit when task percent changed because it's always faster than total percent
        if new_task_percent_done - self.task_percent_done >= 1:
            self.task_percent_done = new_task_percent_done
            self.total_percent_done = new_total_percent_done
            self.progressBarUpdate.emit(self.task_percent_done, self.total_percent_done) # goes to Model

        # check if task has ended
        if task_remaining_time < (self.qtimer_timeout / 1000) or task_remaining_time < 0:   # DONT FORGET TO CHANGE
            self.task_ended()

    def task_ended(self):
        # Do some arduino things
        # Check if there are other tasks, if so, change task
        if len(self.tasks) > (self.running_task + 1):
            print("GO TO NEXT TASK")
            self.running_task += 1
            self.startNextTask.emit(self.running_task)
            self.run_task()
        else:
            # some signals to inform user
            print("ALL TASKS ENDED")
            self.timer.stop()
            return


""" FUNCTIONS """

def calculate_duration(tasklist, return_seconds=False):
    durations = [0, 0, 0]  # days, hours, minutes
    if type(tasklist) is not list:
        tasks = [tasklist]
    else:
        tasks = tasklist
    for t in tasks:
        durations[0] = durations[0] + int(t.duration[0:2])  # days
        durations[1] = durations[1] + int(t.duration[2:4])  # hours
        durations[2] = durations[2] + int(t.duration[4:6])  # minutes

    minutes, hours = durations[2] % 60, durations[2] // 60
    hours, days = durations[1] % 24 + hours, durations[1] // 24
    days = durations[0] + days

    if return_seconds:
        s_time = days * 8.64e4 + hours * 3.6e3 + minutes * 60
        return s_time

    return days, hours, minutes
