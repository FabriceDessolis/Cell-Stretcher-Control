import os
from gpiozero import DigitalInputDevice
import bme280
import time
import serial
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtWidgets import *
import pyqtgraph as pg
import threading

class Monitoring(QWidget):
    """ VARIABLES """
    save_data = True  # Save datas in a txt file
    first_acquisition = True  # save the first epoch on top of data file
    utc_offset = -time.time() - 3600 - 3600  # used for the x axis timestamp, -3600 because gmt+1
    x = []  # x_axis
    data = [[], [], []]  # datas to be plotted and saved : frequency, temp, humidity
    times_storage = []  # refreshed every now and so, save the epochs when the sensor is activated
    flush_storage_delay = 5000  # ms
    run_loop = True  # to stop the thread execution on window close
    sensor_pin = 17  # RPi pin for the sensor

    """ PLOTTER CONFIGURATION """
    # Window creation
    app = pg.mkQApp("NEMA08 humidity tests")
    w = pg.GraphicsLayoutWidget()
    w.resize(1200, 800)

    pg.graphicsItems.DateAxisItem.makeSStepper(500)
    # Plots
    p1 = w.addPlot(title="frequency")
    p1.showGrid(x=True, y=True)
    p1.setAxisItems(axisItems={"bottom": pg.DateAxisItem(utcOffset=utc_offset)})
    w.nextRow()

    p2 = w.addPlot(title="temperature")
    p2.showGrid(x=True, y=True)
    p2.setAxisItems(axisItems={"bottom": pg.DateAxisItem(utcOffset=utc_offset)})
    w.nextRow()

    p3 = w.addPlot(title="humidity")
    p3.showGrid(x=True, y=True)
    p3.setAxisItems(axisItems={"bottom": pg.DateAxisItem(utcOffset=utc_offset)})

    # Create links for X-axis
    p2.setXLink(p1)
    p3.setXLink(p1)

    f_curve = p1.plot()  # freq
    t_curve = p2.plot()  # temp
    h_curve = p3.plot()  # humidity

    # Create mouse hovering infos
    vLine = pg.InfiniteLine(angle=90, movable=False)
    p1.addItem(vLine, ignoreBounds=True)
    p2.addItem(vLine, ignoreBounds=True)
    p3.addItem(vLine, ignoreBounds=True)

    """ SETUP GPIO """
    sensor = DigitalInputDevice(pin=sensor_pin, pull_up=True)

    """ PREPARE A FILE FOR DATA SAVE """
    # txt format will be like "data_DD-MM-YY_HH-MM" to prevent the creation of too many files while testing
    # 1 : check save_datas bool
    # 2 : check if a file already exist within the last minutes
    # 3 : if not create that txt file
    # 4 : first line will be first acquisition epoch, other lines will be datas
    save_folder = "saved_datas"
    file_name = "09-04-24_16h32-with_medium_to_check_evaporation.txt"
    if save_data:
        file = open(f"{save_folder}/{file_name}", "a")

    """ SERIAL READ THREAD """

    def capture_sensor():
        # Starting time of program
        past_value = int
        while run_loop:
            try:
                value = sensor.value
            except:
                return
            if value != past_value:
                if value == 1:
                    times_storage.append(time.time())
                past_value = value

    th = threading.Thread(target=capture_sensor, args='')
    th.start()

    """ PLOT FROM TIME STORAGE DATAS """

    def calculate_values():
        # frequency
        global times_storage
        intervals_storage = []
        print("times_storage :", times_storage)
        while len(times_storage) > 1:
            intervals_storage.append(round((times_storage[1] - times_storage[0]), 2))
            del times_storage[0]
        times_storage = []

        try:
            mid_frequency = round(1 / ((sum(intervals_storage) / len(intervals_storage))), 2)
        except ZeroDivisionError:
            mid_frequency = 0
        print("mid_frequency :", mid_frequency)

        # temp and humidity
        try:
            temperature, pression, humidity = bme280.readBME280All()
            temperature = round(temperature, 2)
            humidity = round(humidity, 2)
        except:
            temperature = 0
            humidity = 0
        th = threading.Thread(target=plot_and_save, args=(mid_frequency, temperature, humidity))
        th.start()
        th.join()

    def plot_and_save(mid_frequency, temperature, humidity):
        # fill up curves
        if x == []:
            x.append(1)
        else:
            x.append(x[-1] + flush_storage_delay / 1000)  # to scale the dateaxis with the refresh delay
        data[0].append(mid_frequency)
        data[1].append(temperature)
        data[2].append(humidity)
        f_curve.setData(x, data[0])
        t_curve.setData(x, data[1])
        h_curve.setData(x, data[2])

        # save in file
        if save_data:
            write_in_file(mid_frequency, temperature, humidity)

    flush_counter = 0

    def write_in_file(freq, temp, humi):
        global first_acquisition, flush_counter
        if first_acquisition:
            t = time.time()
            file.write(f"{t}\n")
            first_acquisition = False
        file.write(f"{freq}, {temp}, {humi}\n")

        # Force save in file in case programm crashes :
        flush_counter += 1
        if flush_counter == 12:  # every minute
            file.flush()
            flush_counter = 0

    """ QTIMER FOR FUNCTION CALL ON GIVEN INTERVALS """
    # The QTimer class provides a high-level programming interface for timers.
    # To use it, create a QTimer , connect its timeout() signal to the appropriate slots, and call start() .
    # From then on, it will emit the timeout() signal at constant intervals.
    timer = pg.QtCore.QTimer()
    timer.timeout.connect(calculate_values)
    timer.start(flush_storage_delay)  # milliseconds

    """ ARDUINO SERIAL TO START / STOP MOTORS """
    arduino_connected = False
    try:
        arduino = serial.Serial('/dev/ttyACM0', 115200)
    except:
        print("Couldn't connect to arduino")
    finally:
        print("Connected to arduino")

    def start_motors():
        global arduino_connected
        time.sleep(1)
        arduino.write(str.encode("1"))
        print("Sending '1' to arduino")
        arduino_connected = True

    def stop_motors():
        arduino.write(str.encode("0"))
        arduino.close()