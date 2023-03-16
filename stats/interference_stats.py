from serial import Serial, SerialException
from threading import Thread
import multiprocessing

FRAMES_AMOUNT = 50

BAUDRATE = 115200

SERIAL_PORT_1 = "COM8"
SERIAL_PORT_2 = "COM5"

ANCHOR_ADDRESS_1 = "AA:04"
ANCHOR_ADDRESS_2 = "AA:05"

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
    
    t1 = multiprocessing.Process(target=serial_read_write, args=(message_1, "./stats/" + file_name_prefix + "_" + str(FRAMES_AMOUNT) + "_1.txt", serial_1))
    t2 = multiprocessing.Process(target=serial_read_write, args=(message_2, "./stats/" + file_name_prefix + "_" + str(FRAMES_AMOUNT) + "_2.txt", serial_2))

    print("Starting t1...")
    t1.start()
    # print("t1 started")
    # print("Starting t2...")
    t2.start()
    print("t2 started")

    t1.join()
    print("t1 joined")
    t2.join()
    print("t2 joined")


print("All done")