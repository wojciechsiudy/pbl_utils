from .mapping import GpsData, Point, GPSConnection, select_points, calculate_position
from .ranging import UwbConnection, UwbDataPair
from .inercing import AhrsConnection, AhrsData

import signal
import sys

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

    def __repr__(self) -> str:
        val =   "================SpauFrame================\n"
        val +=  "                   UWB\n"
        val +=  str(self.uwb_data_pair) + "\n"
        val +=  "                   AHRS\n"
        val +=  str(self.ahrs_data) + "\n"
        val +=  "                   GPS\n"
        val +=  str(self.gps_data) + "\n"
        val +=  "             CALCULATED_POSITION\n"
        val +=  str(self.calculated_position) + "\n"
        return val

    def _validate_intupts(self):
        try:
            if  self.uwb_data_pair.nearest.validate_age() \
            and self.uwb_data_pair.second.validate_age() \
            and self.ahrs_data.validate_age() \
            and self.gps_data.validate_age():
                self.is_valid = True
            else:
                self.is_valid = False
        except AttributeError: # when some conversion failed
            self.is_valid = False

    def calculate(self, points_pair):
        self.calculated_position = calculate_position(self.gps_data, self.uwb_data_pair, points_pair)


class Spausync:
    def __init__(self):
        self.uwb_connection = UwbConnection()
        self.ahrs_connection = AhrsConnection()
        self.gps_connection = GPSConnection(mock = True)
        signal.signal(signal.SIGINT,self.end)

    def launch(self):
        """
        Method initializing all submodules
        """
        self.uwb_connection.connect()
        self.gps_connection.begin()
        # the rest is connected via consructors

    def get_all_data(self) -> SpauData:
        """
        Method invoked when final user ask

        MPerforming calculations and data exchange
        """
        points_to_talk = select_points(self.gps_connection.get_last_value())
        self.uwb_connection.ask_for_distances(points_to_talk[0].address, points_to_talk[1].address)
        data = SpauData(
            self.uwb_connection.get_last_UwbDataPair(),
            self.ahrs_connection.get_last_value(),
            self.gps_connection.get_last_value()
        )
        data.calculate(points_to_talk)
        return data

    def end(self, sig, frame):
        """
        Handle CTRL+C signal.
        """
        print("We requested for an end.")
        self.ahrs_connection.end()
        self.uwb_connection.end()
        self.gps_connection.end()
        sys.exit(0)


    
