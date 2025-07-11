import serial
import time

class Arduino:
    PORT = "/dev/ttyAMA0"
    BAUDRATE = 115200
    TIMEOUT = 2

    def __init__(self):
        print("ARDUINO init")
        try:
            self.ser = serial.Serial(self.PORT, self.BAUDRATE, timeout=self.TIMEOUT)
            self._connect()
        except Exception as e:
            print(e)

    def _connect(self):
        self.ser.open()

    def _disconnect(self):
        self.ser.close()

    def write_read(self, x):
        self.ser.write(str.encode(f'<{x}>\n'))

    def start_task(self, task):
        mode = task.mode                # int
        min_s = task.min_stretch        # float
        max_s = task.max_stretch        # float
        freq = task.freq                # float
        ramp = task.ramp                # float
        hold = task.hold                # float
        duration = task.duration

        message = f'{mode},{min_s},{max_s},{freq},{ramp},{hold},{duration}'

        self.write_read(message)

    def pause(self):
        self.write_read("p")

    def resume(self):
        self.write_read("r")

    def abort(self):
        self.write_read("a")

if __name__ == '__main__':
    a = Arduino()
    try:
        a._connect()
    except Exception as e:
        print(e)