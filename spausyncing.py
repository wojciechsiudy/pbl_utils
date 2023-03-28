from  multiprocessing import Process, Queue

from .mapping import GpsData, Point, get_gps_position, calculate_position
from .ranging import UwbConnection, UwbDataPair
from .inercing import AhrsConnection, AhrsData
from .misc import StampedData

class SpauData:
    def __init__(self,
                 uwb: UwbDataPair,
                 ahrs: AhrsData,
                 gps: GpsData):
        self.uwb_data_pair = uwb
        self.ahrs_data = ahrs
        self.gps_data = gps
        self._validate_intupts()
        self.calculated_position = Point(0.0, 0.0, "NOT_CALCULATED")

    def _validate_intupts(self):
        if  self.uwb_data_pair.nearest.validate_age() \
        and self.uwb_data_pair.second.validate_age() \
        and self.ahrs_data.validate_age() \
        and self.gps_data.validate_age():
            self.is_valid = True
        else:
             self.is_valid = False


class Spausync:
    def __init__(self):
        self.uwb_connection = UwbConnection()
        self.ahrs_connection = AhrsConnection()

    def launch(self):
        """
        Method initializing all submodules
        """
        self.uwb_connection.connect()

    def get_all_data(self) -> SpauData:
        """
        Method invoked when final user ask.
        """
        return SpauData(
            self.uwb_connection.get_last_UwbDataPair(),
            self.ahrs_connection.get_last_value(),
            "self.gps_connection.get_last_value()"
        )

    
