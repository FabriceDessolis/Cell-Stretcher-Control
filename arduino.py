import serial
import time

class Arduino:
    PORT = ""
    BAUDRATE = 9600
    TIMEOUT = 2

    def __init__(self):
        self.ser = serial.Serial()

    def _connect(self):
        self.ser.port = self.PORT
        self.ser.baudrate = self.BAUDRATE
        self.ser.timeout = self.TIMEOUT
        self.ser.open()

    def _disconnect(self):
        ...

    def write_read(self, x):
        ...

    def start_task(self, task):
        mode = task.mode                # int
        min_s = task.min_stretch        # float
        max_s = task.max_stretch        # float
        freq = task.freq                # float
        ramp = task.ramp                # float
        hold = task.hold                # float

        self.ser.write("")

    def pause(self):
        ...

    def resume(self):
        ...

    def abort(self):
        ...

if __name__ == '__main__':
    a = Arduino()
    try:
        a._connect()
    except Exception as e:
        print(e)