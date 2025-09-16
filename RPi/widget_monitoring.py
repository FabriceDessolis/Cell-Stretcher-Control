import os
try:
    import bme280
except:
    pass
import time
import serial
from pyqtgraph.Qt import QtCore, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject
import pyqtgraph as pg
import threading


class MonitoringWidget(QFrame, QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

        """ === INITIALISATION DES VARIABLES === """
        self.save_data = False
        self.first_acquisition = True
        self.utc_offset = -time.time() - 3600 - 3600  # GMT+1
        self.x = []
        self.data = [[], []]  # temp, humidity
        self.times_storage = []
        self.flush_storage_delay = 5000  # ms
        self.run_loop = True
        self.flush_counter = 0

        self.save_folder = "saved_datas"
        self.file_name = "09-04-24_16h32-with_medium_to_check_evaporation.txt"
        if self.save_data:
            os.makedirs(self.save_folder, exist_ok=True)
            self.file = open(f"{self.save_folder}/{self.file_name}", "a")

        """ === PLOTTER CONFIGURATION === """
        self.setup_plots()

        """ === TIMER POUR LA MISE À JOUR DES DONNÉES === """
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.calculate_values)
        self.timer.start(self.flush_storage_delay)

    def setup_plots(self):
        layout = QVBoxLayout(self)
        self.plot_widget = pg.GraphicsLayoutWidget()
        self.plot_widget.resize(1200, 800)
        layout.addWidget(self.plot_widget)

        pg.graphicsItems.DateAxisItem.makeSStepper(500)

        # === Combined Temperature and Humidity Plot ===
        self.p1 = self.plot_widget.addPlot(title="Temperature & Humidity")
        self.p1.showGrid(x=True, y=True)
        self.p1.setAxisItems(axisItems={"bottom": pg.DateAxisItem(utcOffset=self.utc_offset)})

        # === Link X Axis (not necessary as it's a single plot) ===
        # No need for link since we combine everything in p1

        # === Courbes pour Température et Humidité ===
        self.t_curve = self.p1.plot(pen=pg.mkPen('r', width=2), name="Temperature")
        self.h_curve = self.p1.plot(pen=pg.mkPen('b', width=2), name="Humidity")

        # === Ajouter une légende ===
        self.p1.addLegend()

        # === Mouse Hover Line ===
        self.vLine = pg.InfiniteLine(angle=90, movable=False)
        self.p1.addItem(self.vLine, ignoreBounds=True)

    def calculate_values(self):
        try:
            temperature, pression, humidity = bme280.readBME280All()
            temperature = round(temperature, 2)
            humidity = round(humidity, 2)
        except Exception as e:
            print("Error reading BME280:", e)
            temperature = 0
            humidity = 0

        th = threading.Thread(target=self.plot_and_save, args=(temperature, humidity))
        th.start()
        th.join()

    def plot_and_save(self, temperature, humidity):
        if not self.x:
            self.x.append(1)
        else:
            self.x.append(self.x[-1] + self.flush_storage_delay / 1000)

        self.data[0].append(temperature)
        self.data[1].append(humidity)

        self.t_curve.setData(self.x, self.data[0])
        self.h_curve.setData(self.x, self.data[1])

        if self.save_data:
            self.write_in_file(temperature, humidity)

    def write_in_file(self, temp, humi):
        if self.first_acquisition:
            t = time.time()
            self.file.write(f"{t}\n")
            self.first_acquisition = False

        self.file.write(f"{temp}, {humi}\n")

        self.flush_counter += 1
        if self.flush_counter >= 12:
            self.file.flush()
            self.flush_counter = 0

    def closeEvent(self, event):
        """ Stop thread and cleanup on widget close """
        self.run_loop = False
        self.sensor_thread.join()
        if self.save_data:
            self.file.flush()
            self.file.close()
        event.accept()