from multiprocessing import Queue
from threading import Thread
from serial import Serial, SerialException
from time import sleep

BAUDRATE = 115200
MAX_FAILS = 1
FRAMES_AMOUNT = 10
THREAD_TIMEOUT = 0.6

DEBUG = True


class UwbSerialConnection:
    def __init__(self, serial_path="/dev/UWBt") -> None:
        self.serial_path = serial_path
        self.serial = Serial()
        self.connected = False
        self.distances_queue = Queue()
        self.last_value = 0
        self.fails = 0
        self.address_queue = Queue()
        self.last_address = "none"
        self.alive_ping = Queue()
        self._set_threads()

    def begin(self):
        self._connect()
        self.process.start()
        self.watchdog.start()

    def _set_threads(self):
        self.watchdog = Thread(target=self._watchdog_process, args=(self.alive_ping,))
        self.process = Thread(target=self._thread_process,
                              args=(self.distances_queue, self.address_queue, self.alive_ping,))

    def end(self):
        self._disconnect()
        self._set_threads()

    def restart(self):
        self.end()
        self.begin()
        if DEBUG is True:
            print("RESTARTED")

    def _watchdog_process(self, ping_queue):
        while True:
            if ping_queue.qsize() > MAX_FAILS:
                self.restart()
                return
            sleep(THREAD_TIMEOUT)

    def _thread_process(self, queue, address, ping_queue):
        current_address = self.last_address
        while True:
            if DEBUG is True:
                print("THREAD ", self.serial_path, " ALIVE, address set: ", current_address)
            if ping_queue.qsize() > 0:
                ping_queue.get("X")
            if self.address_queue.qsize() > 0:
                current_address = address.get()
                if DEBUG:
                    print("ADDRESS SET: ", current_address)
            message = str(current_address) + str(FRAMES_AMOUNT)
            if self.serial.isOpen() and current_address != "none":
                try:
                    if self.serial_path == "/dev/UWBl":
                        sleep(0.007)
                        if DEBUG:
                            print("SMALL SLEEP")
                    elif self.serial_path == "/dev/UWBr":
                        sleep(0.053)
                        if DEBUG:
                            print("DEEP SLEEP")
                    #begin communication
                    self.serial.write(bytes(message, "ASCII"))
                    for i in range(0, FRAMES_AMOUNT):
                        line = str(self.serial.readline(), encoding="ASCII")
                        try:
                            data = line.split('|')
                            distance = data[1]
                            if DEBUG:
                                print("I: ", i, "DISTANCE: ", distance)
                            queue.put(distance)
                        except (ValueError, IndexError):  # in case of reciver failure
                            print("error")
                except(TypeError, SerialException, OSError):
                    if DEBUG:
                        print("SERIAL FAILURE")
                    return
            else:
                self.reconnect()
            sleep(THREAD_TIMEOUT)

    def _connect(self):
        self.serial = Serial(self.serial_path, BAUDRATE)
        self.connected = True

    def _disconnect(self):
        self.serial.close()
        self.connected = False

    def reconnect(self):
        self.fails = 0
        self._disconnect()
        self._connect()

    def _test_connection(self):
        if self.serial.isOpen():
            self.connected = True
        else:
            self.connected = False

    # this method creates interface between ROS2 and serial connection
    def get_distance(self):
        if self.distances_queue.qsize() > 0:
            self.last_value = self.distances_queue.get()
        return self.last_value

    def set_address(self, _address):
        if _address != self.last_address:
            self.last_address = _address
            self.address_queue.put(self.last_address)
            if DEBUG:
                print("SET_ADDRESSS_CALLED: ", _address)
        self.alive_ping.put("X")


