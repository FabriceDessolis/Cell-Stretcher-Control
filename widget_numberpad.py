import sys
import os
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSignal
from ressources.numberpad import Ui_Form
from pop_up_dialog import Dialog

class NumberPad(QWidget, Ui_Form):
    closeWidget = pyqtSignal(object)
    
    def __init__(self, *args, obj=None, **kwargs):
        super(NumberPad, self).__init__(*args, **kwargs)
        self.setupUi(self)
        
        self._type = None
        self.value = ""
        
        # Connect signals        
        numbers_list = ["00", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "dot"]
        for number in numbers_list:
            getattr(self, f"pushButton_{number}").clicked.connect(lambda foo, number=number: self.add_number(number))
            
        self.pushButton_erase.clicked.connect(self.delete_number)
        self.pushButton_enter.clicked.connect(self.enter)
        self.pushButton_cancel.clicked.connect(self.cancel)
    
    def add_number(self, number):
        if number == "dot":
            number = "."
        
        self.value += number
        self.update_display()
    
    def delete_number(self):
        self.value = self.value[:-1]
        self.update_display()
    
    def update_display(self):
        self.lineEdit.setText(self.value)
        
    def enter(self):
        if self._type == "not_duration":
            try:
                num_value = float(self.value)
            except Exception as e:
                Dialog(str(e))
                return
        if self._type == "duration":
            if self.value.isnumeric() is False:
                Dialog("Please enter a date with DDHHMN format")
                return
            if len(self.value) != 6:
                Dialog("Please enter a date with DDHHMN format")
                return
            num_value = self.value
                    
        self.closeWidget.emit(num_value) # events init
        self.value = ""
        self.update_display()
    
    def cancel(self):
        self.closeWidget.emit(None)
        self.value = ""
        self.update_display()
        
    def closeEvent(self, event):
        self.cancel()

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = NumberPad()
    view.show()
    sys.exit(app.exec())