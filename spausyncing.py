from  multiprocessing import Process

from .mapping import Point, get_gps_position, calculate_position
from .ranging import UwbConnection, UwbDataPair
# from .inercing import AhrsConnection, AhrsData # module not ready

class Spausync:
    def __init__(self):
        self.uwb_connection = UwbConnection()
        #self.ahrs_connection = AhrsConnection()

    def launch(self):
        self.uwb_connection.connect()

    
