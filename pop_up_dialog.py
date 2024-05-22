import sys
from PyQt5.QtWidgets import *

class Dialog(QDialog):
    def __init__(self, text, abort_button=False):
        super().__init__()
        self.setWindowTitle(" Oh no :( ")
        self.setMinimumHeight(200)
        self.setStyleSheet("font: 20pt;")
        self.setModal(True)
        if abort_button:
            Qbtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        else:
            Qbtn = QDialogButtonBox.Ok
        self.buttonBox = QDialogButtonBox(Qbtn)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        message = QLabel(text)
        self.layout.addWidget(message)
        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)
        self.result = self.exec()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    view = Dialog("test", True)
    print(view.result)