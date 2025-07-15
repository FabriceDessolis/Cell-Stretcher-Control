from arduino import Arduino
from methods import *
from PyQt5.QtCore import *

class TaskManager(QObject):
    qtimer_timeout = 1000 # 1s
    progressBarUpdate = pyqtSignal(float, float)
    timesUpdate = pyqtSignal(tuple)
    startNextTask = pyqtSignal(int)
    allTaskEnded = pyqtSignal()
    
    def connect_to_arduino(self):
        self.arduino = Arduino()

    def init(self, task_list):
        print("TASK MANAGER")
        self.tasks = task_list # collection of Task objects
        self.running_task = 0 # for index

        self.times_track = {"task": {"start_time": 0,            # epoch in seconds
                                     "end_time": 0,              # epoch in seconds
                                     "duration": 0,              # seconds
                                     "percent_done": 0,          # %
                                     "time_elapsed": 0,          # s
                                     "time_left": 0},            # s
                            "total": {"start_time": 0,
                                      "end_time": 0,
                                      "duration": 0,
                                      "percent_done": 0,
                                      "time_elapsed": 0,
                                      "time_left": 0},
                            "pause": 0}                          # epoch in seconds

        self.times_track["total"]["duration"] = calculate_duration(self.tasks, return_seconds=True)
        self.run_new_task()

        self.timer = QTimer()
        self.timer.timeout.connect(self.check_remaining_time)
        self.timer.setInterval(self.qtimer_timeout)
        self.timer.start()

    def run_new_task(self):
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

        self.arduino.start_task(self.tasks[self.running_task])

    def pause_process(self):
        # Store the epoch when the program was paused
        self.times_track["pause"] = QDateTime.currentSecsSinceEpoch()
        # Stop the QTimer
        self.timer.stop()
        self.arduino.pause()

    def resume_process(self):
        # Get the duration the process was paused and add it to the previously stored times
        pause_duration = QDateTime.currentSecsSinceEpoch() - self.times_track["pause"]
        for key, item in self.times_track.items():
            if key != "pause":
                item["start_time"] += pause_duration
                item["end_time"] += pause_duration
        # Restart the QTimer
        self.timer.start()
        self.arduino.resume()

    def abort_process(self):
        self.timer.stop()
        self.arduino.abort()

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

        self.times_track["task"]["time_elapsed"] = new_task_time_elapsed
        self.times_track["total"]["time_elapsed"] = new_total_time_elapsed
        task_time_elapsed_string = return_string_duration(self.times_track["task"]["time_elapsed"])
        task_time_remaining_string = return_string_duration(self.times_track["task"]["time_left"])
        total_time_elapsed_string = return_string_duration(self.times_track["total"]["time_elapsed"])
        total_time_remaining_string = return_string_duration(self.times_track["total"]["time_left"])
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
            self.run_new_task()
        else:
            # some signals to inform user
            print("ALL TASKS ENDED")
            self.allTaskEnded.emit()
            self.progressBarUpdate.emit(100, 100) # make sure it's not stuck at 99
            self.timer.stop()