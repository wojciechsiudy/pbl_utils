"""
authors: Maciej Bolesta, Wojciech Siudy
"""

from serial import Serial
from multiprocessing import Queue
from threading import Thread

from .misc import StampedData

class InercialPoint:
    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        self.x = x
        self.y = y
        self.z = z

class AhrsData(StampedData):
    def __init__(self,
                 accel: InercialPoint,
                 gyro: InercialPoint,
                 mag: InercialPoint):
        self.accel = accel
        self.gyro = gyro
        self.mag = mag

class AhrsConnection:
    def __init__(self, serial_path="/dev/AHRS"):
        self.ahrs_serial = Serial(serial_path, 115200)
        self.measures_queue = Queue()
        self.last_value = AhrsData() # todo: initialisation
        self._set_threads()
        
    def begin(self):
        self.process.start()
        
    def _set_threads(self):
        self.process = Thread(target=self._thread_process, args=(self.measures_queue,))
        
    def _thread_process(self, queue):
        while True:
            try:
                line = str(self.ahrs_serial.readline(), encoding="ASCII")
                if "AHRS" in line:
                    data = line.split(';')
                    queue.put(self.ahrs_data_to_point(data))
            except:
                print("readErr")

    def end(self):
        self._set_threads()
        
        
    def getLastValue(self):
        if self.measures_queue.qsize() > 0:
            self.last_value = self.measures_queue.get()
        return self.last_value
        
    def ahrs_data_to_point(self, data):
        a = InercialPoint()
        g = InercialPoint()
        m = InercialPoint()
        try:
            m.x = float(data[1])
            m.y = float(data[2])
            m.z = float(data[3])
            g.x = float(data[4])
            g.y = float(data[5])
            g.z = float(data[6])
            a.x = float(data[7])
            a.y = float(data[8])
            a.z = float(data[9])
        except:
            pass    
        return AhrsData(a, g, m)       



