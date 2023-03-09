from serial import Serial, SerialException
from threading import Thread

FRAMES_AMOUNT = 100

BAUDRATE = 115200

SERIAL_PORT_1 = "COM12"
SERIAL_PORT_2 = "COM8"

ANCHOR_ADDRESS_1 = "AA:05"
ANCHOR_ADDRESS_2 = "AA:04"

def serial_read_write(message, filename, serial):
    serial.write(bytes(message, "ASCII"))
    lines = ""
    for _ in range(FRAMES_AMOUNT):
        lines += str(serial.readline(), encoding="ASCII")

    f = open(filename, "w+")
    f.write(lines)
    f.close()

    serial.close()

iterations = int(input("Input iterations number\n"))
file_name_prefix = input("Input filename prefix\n")

for i in range(iterations):
    message_1 = ANCHOR_ADDRESS_1 + str(FRAMES_AMOUNT)
    message_2 = ANCHOR_ADDRESS_2 + str(FRAMES_AMOUNT)

    serial_1 = Serial(SERIAL_PORT_1, BAUDRATE)
    serial_2 = Serial(SERIAL_PORT_2, BAUDRATE)
    
    t1 = Thread(target=serial_read_write, args=(message_1, file_name_prefix + "_1.txt", serial_1))
    t2 = Thread(target=serial_read_write, args=(message_2, file_name_prefix + "_2.txt", serial_2))

    t1.start()
    t2.start()

    t1.join()
    t2.join()


print("All done")