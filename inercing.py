"""
authors: Maciej Bolesta, Wojciech Ptaś, Wojciech Siudy
"""

from sys import stdout
from serial import Serial
from multiprocessing import Queue, Process

from .misc import StampedData

class AhrsReadError(Exception):
    pass

class InercialPoint:
    def __init__(self, x = 0.0, y = 0.0, z = 0.0):
        self.x = x
        self.y = y
        self.z = z

class AhrsData(StampedData):
    def __init__(self,
                 accel = InercialPoint(),
                 gyro = InercialPoint(),
                 mag = InercialPoint()):
        super().__init__()
        self.accel = accel
        self.gyro = gyro
        self.mag = mag

    def __repr__(self) -> str:
        value = ""
        value = value + str(self.accel.x) + ", "
        value = value + str(self.accel.y) + ", "
        value = value + str(self.accel.z) + ", "
        value = value + str(self.gyro.x) + ", "
        value = value + str(self.gyro.y) + ", "
        value = value + str(self.gyro.z) + ", "
        value = value + str(self.mag.x) + ", "
        value = value + str(self.mag.y) + ", "
        value = value + str(self.mag.z)
        return value

class AhrsConnection:
    def __init__(self, serial_path="/dev/AHRS"):
        self.ahrs_serial = Serial(serial_path, 115200)
        self.measures_queue = Queue(maxsize=10)
        self.last_value = AhrsData()
        self._set_Process()
        self._begin()

    def _begin(self):
        self.process.start()
        
    def _set_Process(self):
        self.process = Process(target=_ahrs_Process, args=(self.ahrs_serial, self.measures_queue,))

    def end(self):
        self._set_Process()
        
    def get_last_value(self):
        if self.measures_queue.qsize() > 0:
            self.last_value = self.measures_queue.get()
        return self.last_value
    

def _ahrs_Process(serial: Serial, queue: Queue):
        while True:
            line = (str(serial.readline(), encoding="ASCII")).strip()
            if "AHRS" in line:
                data = line.split(';')
                if queue.qsize() > 5:
                   queue.get()
                try:
                    queue.put(ahrs_data_to_point(data))
                except AhrsReadError:
                    pass
      
def ahrs_data_to_point(data):
    if len(data) < 9:
        raise AhrsReadError
    a = InercialPoint()
    g = InercialPoint()
    m = InercialPoint()
    m.x = float(data[1])
    m.y = float(data[2])
    m.z = float(data[3])
    g.x = float(data[4])
    g.y = float(data[5])
    g.z = float(data[6])
    a.x = float(data[7])
    a.y = float(data[8])
    a.z = float(data[9])
    return AhrsData(a, g, m)   