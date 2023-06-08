from serial import Serial

serial_device = Serial('/dev/ttyUSB0', 115200)

while True:
    line = str(serial_device.readline(), encoding='ascii')
    print("line: " + line)
