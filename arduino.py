import serial
import time
import threading

class Arduino:
    PORT = '/dev/serial0'
    BAUDRATE = 115200
    TIMEOUT = 2

    def __init__(self):
        print("ARDUINO init")
        try:
            self.ser = serial.Serial(self.PORT, self.BAUDRATE, timeout=self.TIMEOUT)
            print("connected")
        except Exception as e:
            print(f'Erreur connection : {e}')
            
        th = threading.Thread(target=self.read_serial, args=())
        th.start()

    def _connect(self):
        self.ser.open()

    def _disconnect(self):
        self.ser.close()

    def write_read(self, message):
        msg = f'<{message}>\n'
        try:
            self.ser.write(msg.encode())
        except Exception as e:
            print(e)
            
    def read_serial(self):
        while True:
            if self.ser.inWaiting() > 0:
                print("message received from esp :")
                line = self.ser.readline().decode().strip()
                print(line)


    def start_task(self, task):
        mode = task.mode                # int
        min_s = task.min_stretch        # floats
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