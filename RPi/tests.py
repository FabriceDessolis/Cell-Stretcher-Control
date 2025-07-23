import sys
import serial.tools.list_ports

print(sys.platform)
ports = []
for port in serial.tools.list_ports.comports():
    ports.append(port.name)
print(ports)

MAX_STRETCH = 30

text = "The max stretch can't go over %s %%" % MAX_STRETCH

print(text)