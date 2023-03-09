from serial import Serial, SerialException
from threading import Thread

FRAMES_AMOUNT = 100

SERIAL_PORT_1 = "COM5"
SERIAL_PORT_2 = "COM6"

ANCHOR_ADDRESS_1 = "AA:BB"
ANCHOR_ADDRESS_2 = "CC:DD"

def serial_read_write(message, filename):
    Serial.serial.write(bytes(message, "ASCII"))
    lines = ""
    for _ in range(FRAMES_AMOUNT):
        lines += str(Serial.serial.readline(), encoding="ASCII")

    f = open(filename, "w+")
    f.write(lines)
    f.close()   

iterations = int(input("Input iterations number\n"))
file_name_prefix = input("Input filename prefix\n")

for i in range(iterations):
    message_1 = str(ANCHOR_ADDRESS_1) + str(FRAMES_AMOUNT)
    message_2 = str(ANCHOR_ADDRESS_2) + str(FRAMES_AMOUNT)
    
    t1 = Thread(target=serial_read_write, args=(message_1, file_name_prefix + "1"))
    t2 = Thread(target=serial_read_write, args=(message_2, file_name_prefix + "2"))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

print("All done")