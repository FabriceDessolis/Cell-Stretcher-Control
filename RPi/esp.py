import serial
import time
import threading
from pop_up_dialog import Dialog
from PyQt5.QtCore import *
import sys

PORT = 'COM12' if sys.platform == "win32" else '/dev/serial0'
BAUDRATE = 115200
TIMEOUT = 2

class ESP(QObject):
    stepperPosition = pyqtSignal(str)
    def __init__(self):
        super(ESP, self).__init__()
        print("ESP init")
        self.connected = False
        self.ser = serial.Serial()
        self._connect()

    def _connect(self):
        try:
            self.ser.port, self.ser.baudrate, self.ser.timeout = PORT, BAUDRATE, TIMEOUT
            self.ser.open()
            self.th = threading.Thread(target=self.read_serial, args=())
            self.th.start()
            self.connected = True
            print("ESP connected")
        except Exception as e:
            print(f'Erreur connection : {e}')

    def _disconnect(self):
        self.ser.close()
        self.connected = False
        print("ESP disconnected")

    def write(self, message):
        if not self.connected:
            Dialog("Please connect to the ESP first")
            return
        msg = f'<{message}>\n'
        try:
            self.ser.write(msg.encode())
        except Exception as e:
            print(e)
            
    def read_serial(self):
        while self.connected:
            if self.ser.inWaiting() > 0:
                line = self.ser.readline().decode().strip()
                # actual position will be in steps and of the form <4234>
                if line[0] == '<' and line[-1] == '>':
                    for character in "<>" :
                        line = line.replace(character, "")
                        self.stepperPosition.emit(line)
            time.sleep(0.2)


    def start_task(self, task):
        mode = task.mode                # int
        min_s = task.min_stretch        # float
        max_s = task.max_stretch        # float
        freq = task.freq                # float
        ramp = task.ramp                # float
        hold = task.hold                # float
        duration = task.duration

        message = f'{mode},{min_s},{max_s},{freq},{ramp},{hold},{duration}'

        self.write(message)

    def pause(self):
        self.write("p")

    def resume(self):
        self.write("r")

    def abort(self):
        self.write("a")

    def go_to_position(self, position):
        # position in stretch percent
        message = f'g{position}'
        self.write(message)

if __name__ == '__main__':
    a = ESP()