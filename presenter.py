from PyQt5.QtCore import pyqtSlot
from pop_up_dialog import Dialog

class Presenter:
    """ Stores dictionaries, selected buttons, applied values, and manages communications between the view and
        the taskmanager
    """
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.model.giveTaskToView.connect(lambda item, task: self.view.create_task(item, task))
        self.model.removeTaskFromView.connect(lambda item: self.view.remove_task(item))
        self.model.progressBarUpdate.connect(lambda task, total: self.view.update_progress_bar(task, total))
        self.model.timesUpdate.connect(lambda times: self.view.update_times(times))
        self.model.startNextTask.connect(lambda index: self.view.start_next_task(index))
        self.model.runStarted.connect(lambda run_state: self.view.start_pause_abort(run_state))
        self.model.allTaskEnded.connect(self.end)

        for i in self.model.settings_buttons.values():
            for j in i:
                self.model.settings_values[j] = None

        # Connect settings buttons, making distinction with the duration buttons
        for _type, numbers in self.model.settings_buttons.items():
            for n in numbers:
                getattr(self.view, f"pushButton_{n}").clicked.connect(lambda x, n=n, _type=_type: self.ask_for_value(n, _type))

        # Connect mode select buttons
        for number, name in self.model.modes.items():
            getattr(self.view, f"pushButton_m{number}").clicked.connect(lambda boolean, number=number: self.mode_changed(number))

        self.view.pushButton_addtask.clicked.connect(self.model.add_new_task)
        self.view.pad.closeWidget.connect(self.apply_value)
        self.view.pushButton_1.clicked.connect(self.duplicate_task)
        self.view.pushButton_2.clicked.connect(self.remove_task)
        self.view.pushButton_4.clicked.connect(self.test)
        self.view.pushButton_start.clicked.connect(self.start_pause)
        self.view.pushButton_abort.clicked.connect(self.abort)
        self.view.pushButton_stepper_go.clicked.connect(self.model.stepper_go)

    def test(self):
        print(self.model.tasks)

    def ask_for_value(self, n: int, _type: str):
        """
        This is called whenever a button is pressed. It shows the numberpad widget
        """
        self.view.pad._type = _type
        self.model.current_button = n
        self.view.show_numberpad()

    def mode_changed(self, number):
        """
        This is called when a mode button is clicked, it changes the selected mode
        """
        self.model.current_mode = number
        self.view.mode_changed(number)

    def apply_value(self, value):
        # value comes as an int if type is "not_duration" or as a string if type is "duration"
        if value is not None:
            # convert to int to remove decimals
            if type(value) is float:
                if value.is_integer():
                    value = int(value)
            # store value in the dictionary
            self.model.settings_values[self.model.current_button] = value
            # and display it
            self.view.display_value(value, self.model.current_button)
            # if we change the stepper distances togo, affect the other button accordingly:
            if self.model.current_button // 10 == 6:
                affected_button, affected_val = self.model.stepper_togo_changed()
                self.view.display_value(affected_val, affected_button)

    def duplicate_task(self):
        items = self.view.listWidget.selectedItems()
        ok = self.check_items_condition(items)
        if ok:
            self.model.duplicate_task(items[0])

    def remove_task(self):
        items = self.view.listWidget.selectedItems()
        ok = self.check_items_condition(items)
        if ok:
            self.model.remove_task(items[0])

    def check_items_condition(self, item: object) -> int:
        # check if there are any task created
        if self.model.tasks == []:
            Dialog("No task was created")
            return 0
        if item == "": # for start button
            return 1
        if not item:
            Dialog("No task was selected")
            return 0
        else:
            return 1

    def start_pause(self):
        if self.model.run_state["running"] is False:
            ok = self.check_items_condition("")
            if not ok:
                return
            items_order = []
            for i in range(self.view.listWidget.count()):
                item = self.view.listWidget.item(i)
                items_order.append(item)
            accepted = self.model.start(items_order)
            if accepted:
                self.view.create_taskrecap_view(items_order)
            else:
                return

        elif self.model.run_state["paused"] is False:
            self.model.run_state["paused"] = True
            self.model.task_manager.pause_process()
            self.view.start_pause_abort(self.model.run_state)

        elif self.model.run_state["paused"] is True:
            self.model.run_state["paused"] = False
            self.model.task_manager.resume_process()
            self.view.start_pause_abort(self.model.run_state)
            
    def end(self):
        self.model.run_state["paused"] = False
        self.model.task_manager.resume_process()
        self.view.start_pause_abort(self.model.run_state)
       

    def abort(self):
        if self.model.run_state["running"] is False:
            return # nothing to abort
        else:
            accepted = Dialog("Are you sure you want to abort the process ?", True).result
            if accepted:
                self.model.run_state["running"] = False
                self.model.run_state["paused"] = False
                # Reset everything to zero
                self.view.clean_after_abort()
                self.model.task_manager.abort_process()
                self.view.start_pause_abort(self.model.run_state)

