from  multiprocessing import Process, Queue

from .mapping import Point, get_gps_position, calculate_position
from .ranging import UwbConnection, UwbDataPair
# from .inercing import AhrsConnection, AhrsData # module not ready

class SpauData:
    def __init__(self) -> None:
        self.uwb_data = ""

class Spausync:
    def __init__(self):
        self.uwb_connection = UwbConnection()
        #self.ahrs_connection = AhrsConnection()

    def launch(self):
        self.uwb_connection.connect()

    def get_spau_info(self):
        pass

    
