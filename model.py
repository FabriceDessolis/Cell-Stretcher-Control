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
    timesUpdate = pyqtSignal(tuple)
    startNextTask = pyqtSignal(int)

    def __init__(self):
        super(Model, self).__init__()
        self.tasks = [] # [[item, task object], [...]]
        self.task_manager = TaskManager() # will be used to hold the TaskManager object
        self.task_manager.progressBarUpdate.connect(lambda task, total: self.progressBarUpdate.emit(task, total))
        self.task_manager.startNextTask.connect(lambda index: self.startNextTask.emit(index))
        self.task_manager.timesUpdate.connect(lambda times: self.timesUpdate.emit(times))

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
            self.task_manager.init(task_list)

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
    timesUpdate = pyqtSignal(tuple)
    startNextTask = pyqtSignal(int)

    def init(self, task_list):
        self.tasks = task_list # collection of Task objects
        self.running_task = 0 # for index

        self.times_track = {"task": {"start_time": 0,            # epoch in seconds
                                     "end_time": 0,              # epoch in seconds
                                     "duration": 0,              # seconds
                                     "percent_done": 0,          # %
                                     "time_elapsed": 0,
                                     "time_left": 0},
                            "total": {"start_time": 0,
                                      "end_time": 0,
                                      "duration": 0,
                                      "percent_done": 0,
                                      "time_elapsed": 0,
                                      "time_left": 0}}

        self.times_track["total"]["duration"] = calculate_duration(self.tasks, return_seconds=True)
        self.run_task()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_remaining_time)
        self.timer.start(self.qtimer_timeout)

    def run_task(self):
        # new task percent done is 0
        self.times_track["task"]["percent_done"] = 0
        self.times_track["task"]["time_elapsed"] = 0
        # Get the epoch where we started and get task duration and end time
        self.times_track["task"]["start_time"] = QDateTime.currentSecsSinceEpoch()
        self.times_track["task"]["duration"] = calculate_duration(self.tasks[self.running_task], return_seconds=True)
        self.times_track["task"]["end_time"] = self.times_track["task"]["start_time"] + self.times_track["task"]["duration"]
        # if it's the first task, find the total end time
        if self.running_task == 0:
            self.times_track["total"]["start_time"] = self.times_track["task"]["start_time"]
            self.times_track["total"]["end_time"] = self.times_track["total"]["start_time"] + self.times_track["total"]["duration"]

    def pause_process(self):
        ...

    def resume_process(self):
        ...

    def abort_process(self):
        ...

    def check_remaining_time(self):
        """
        Called each QTimer timeout interval to check if task is done and update progress bars
        """
        self.times_track["task"]["time_left"] = self.times_track["task"]["end_time"] - QDateTime.currentSecsSinceEpoch()
        self.times_track["total"]["time_left"] = self.times_track["total"]["end_time"] - QDateTime.currentSecsSinceEpoch()
        self.update_view()
        self.has_task_ended()

    def update_view(self):
        # update QProgressBar
        new_task_percent_done = get_percentage(self.times_track["task"]["time_left"], self.times_track["task"]["duration"])
        new_total_percent_done = get_percentage(self.times_track["total"]["time_left"], self.times_track["total"]["duration"])
        # here we only emit when task percent changed because it's always faster than total percent
        if new_task_percent_done - self.times_track["task"]["percent_done"] >= 1:
            self.times_track["task"]["percent_done"] = new_task_percent_done
            self.times_track["total"]["percent_done"] = new_total_percent_done
            self.progressBarUpdate.emit(self.times_track["task"]["percent_done"], self.times_track["total"]["percent_done"]) # goes to Model

        # update time elapsed and time left
        new_task_time_elapsed = self.times_track["task"]["duration"] - self.times_track["task"]["time_left"]
        new_total_time_elapsed = self.times_track["total"]["duration"] - self.times_track["total"]["time_left"]
        if new_task_time_elapsed - self.times_track["task"]["time_elapsed"] >= 59 or self.times_track["task"]["time_elapsed"] == 0:
            print("EMIT")
            self.times_track["task"]["time_elapsed"] = new_task_time_elapsed
            self.times_track["total"]["time_elapsed"] = new_total_time_elapsed
            task_time_elapsed_string = return_string_duration(self.times_track["task"]["time_elapsed"])
            task_time_remaining_string = return_string_duration(self.times_track["task"]["time_left"])
            total_time_elapsed_string = return_string_duration(self.times_track["total"]["time_elapsed"])
            if self.times_track["total"]["time_left"] > 0: # prevents negative value
                total_time_remaining_string = return_string_duration(self.times_track["total"]["time_left"])
            else:
                total_time_remaining_string = ("00", "00", "00")
            self.timesUpdate.emit((task_time_elapsed_string, task_time_remaining_string, total_time_elapsed_string, total_time_remaining_string))

    def has_task_ended(self):
        # check if task has ended
        if self.times_track["task"]["time_left"] < (self.qtimer_timeout / 1000) or self.times_track["task"]["time_left"] < 0:   # DONT FORGET TO CHANGE
            self.task_ended()

    def task_ended(self):
        # Do some arduino things
        # Check if there are other tasks, if so, change task
        if len(self.tasks) > (self.running_task + 1):
            print("GO TO NEXT TASK")
            self.running_task += 1
            self.startNextTask.emit(self.running_task)      # update label in the task recap view
            self.run_task()
        else:
            # some signals to inform user
            print("ALL TASKS ENDED")
            self.timer.stop()
            return


""" FUNCTIONS """

def calculate_duration(tasklist, return_seconds=False):
    """
    task list comes as a list of task objects, we take the instance variable "duration",
    it's a string looking like "120530" -> "DDHHMN"
    """
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

def return_string_duration(seconds):
    """
    kind of the opposite of calculate duration, here we input seconds and output a string "DDHHMN"
    """
    minutes = int(seconds // 60) % 60
    hours = int(seconds // 3600) % 24
    days = int(seconds // 86400)
    l = [days, hours, minutes]
    for i in range(len(l)):
        l[i] = str(l[i])
        if len(l[i]) == 1:
            l[i] = "0" + l[i]
    return l[0], l[1], l[2]
def get_percentage(remaining_time, duration):
    p = 100 - ((remaining_time / duration) * 100)
    return p