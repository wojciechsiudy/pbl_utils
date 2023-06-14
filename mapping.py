import math
import time
import json
from serial import Serial
from geopy.distance import geodesic
from pyproj import Transformer
from multiprocessing import Process, Queue, Value

from .uwb_constants import UwbConstants
#from .pointsDB import getPoints
from .misc import StampedData
from .ranging import UwbDataPair, UwbSingleData

POSITION_RADIUS_M : float = float('inf')
MAX_UWB_OFFSET_FACTOR: float = 1.15


class Point():
    """
    Class holding data about point on Earth surface
    """
    def __init__(self, x: float, y: float , address:str="TAG"):
        self.x = x
        self.y = y
        self.address = address

    def __repr__(self) -> str:
        val =  "x: "    + str(self.x)
        val += " y: "   + str(self.y)
        val += " adr: " + str(self.address)
        return val

    def is_around(self, another):
        distance = get_distance(self, another)
        if (distance > POSITION_RADIUS_M):
            return False
        else:
            return True

class GpsData(Point, StampedData):
    def __init__(self, x: float, y: float, address: str = "TAG"):
        super().__init__(x, y, address)
        StampedData.__init__(self)

    def __repr__(self):
        return str(self.x) + " " + str(self.y)

@staticmethod
def get_GpsData_from_Point(point: Point) -> GpsData:
    return GpsData(point.x, point.y, point.address)

class GPSConnection():
    """
    Class holding GPS connection

    If mock parameter is set True no serial device is
    used - simulation in run instead
    """
    def __init__(self, mock = False) -> None:
        self.settings = UwbConstants()
        self.measures_queue = Queue(maxsize = 10)
        self.last_value = GpsData(0.0, 0.0)
        self.mocking_timer = Value('i', 0)
        if mock:
           self.process = Process(target = mock_gps_position, args = (self.measures_queue, self.mocking_timer))
        else:
            self.gps_serial = Serial(self.settings.get_value("GPS_SERIAL_ADDRESS"), baudrate=9600)
            self.process = Process(target = get_gps_position, args = (self.gps_serial, self.measures_queue))

    def end(self):
        self.process.terminate()
    def begin(self):
        self.process.start()
        print("GPS process started")

    def get_last_value(self):
        if self.measures_queue.qsize() > 0:
            self.last_value = self.measures_queue.get()
        return self.last_value


def select_points(gps_position: Point) -> tuple:
    """
    Function asking database for pair of the nearest points
    based on GPS position
    """
    points_around = []
    points_database = get_points(1)
    if points_database is None:
        raise ValueError("Database is empty")
    for point in points_database:
        distance = get_distance(gps_position, point)
        if distance < float('inf'):
            points_around.append((point, get_distance(gps_position, point)))
    points_around.sort(key=lambda x: x[1])
    nearest = points_around[0][0]
    second = points_around[1][0]
    if len(points_around) > 2:
        third = points_around[2][0]
        return (nearest, second, third)
    else:
        return (nearest, second)


def get_distance(a:Point, b:Point) -> float:
    pa = (a.x, a.y)
    pb = (b.x, b.y)
    return geodesic(pa, pb).m

def calculate_position(gps_data: GpsData, uwb_data: UwbDataPair, points_pair: tuple):
    """
    Function calculating position based on:
        - positions     of anchor_A and anchor_B
        - position      of ctrl_anchor from GPS
        - distances     to anchor_A and anchor_B    in meters
        - power         of anchor_A and anchor_B    in dB

    Using WGS-84 ellipsoid and EPSG2177
    """
    # expand parameters
    try:
        anchor_A        = points_pair[0]
        anchor_B        = points_pair[1]
        ctrl_anchor     = gps_data
        distance_a      = uwb_data.nearest.distance
        distance_b      = uwb_data.second.distance
        power_a         = uwb_data.nearest.power
        power_b         = uwb_data.second.power
    except AttributeError as err:
        return Point(0.0, 0.0, "-1 bad arguments")

    # transform points
    transformer1 = Transformer.from_crs("EPSG:4326", "EPSG:2177")        #transform from WGS84 to PL-2000
    transformer2 = Transformer.from_crs("EPSG:2177", "EPSG:4326")        #transform from PL-2000 to WGS84
    anch_xy_A = transformer1.transform(anchor_A.x, anchor_A.y)
    anch_xy_B = transformer1.transform(anchor_B.x, anchor_B.y)
    ctrlanch_xy = transformer1.transform(ctrl_anchor.x, ctrl_anchor.y)
    scale_offset_factor = 1.005

    d = math.sqrt((anch_xy_B[0] - anch_xy_A[0]) ** 2 + (anch_xy_B[1] - anch_xy_A[1]) ** 2)

    # non intersecting
    if d > distance_a + distance_b:
        while (distance_a + distance_b < d and scale_offset_factor < MAX_UWB_OFFSET_FACTOR):
            if power_a < power_b:
                distance_b *= scale_offset_factor
            elif power_a > power_b:
                distance_a *= scale_offset_factor
            scale_offset_factor += 0.005
    if d > distance_a + distance_b:
        return Point(0, 0, "-2 non-intersecting")
    # One circle within other
    if d < abs(distance_a - distance_b):
        return Point(0, 0, "-3 one circle within other")
    # coincident circles
    if d == 0 and distance_a == distance_b:
        return Point(0, 0, "-4 coincident circles")
    else:
        a = (distance_a ** 2 - distance_b ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(distance_a ** 2 - a ** 2)
        x2 = anch_xy_A[0] + a * (anch_xy_B[0] - anch_xy_A[0]) / d
        y2 = anch_xy_A[1] + a * (anch_xy_B[1] - anch_xy_A[1]) / d
        x3 = x2 + h * (anch_xy_B[1] - anch_xy_A[1]) / d
        y3 = y2 - h * (anch_xy_B[0] - anch_xy_A[0]) / d

        x4 = x2 - h * (anch_xy_B[1] - anch_xy_A[1]) / d
        y4 = y2 + h * (anch_xy_B[0] - anch_xy_A[0]) / d

        #return (x3, y3, x4, y4)
        pa = (x3, y3)
        pb = (x4, y4)
        d1 = math.sqrt((ctrlanch_xy[0] - pa[0]) **2 + (ctrlanch_xy[1] - pa[1]) **2)
        d2 = math.sqrt((ctrlanch_xy[0] - pb[0]) **2 + (ctrlanch_xy[1] - pb[1]) **2)
        if d1 < d2:
            position = transformer2.transform(x3, y3)
            return Point(position[0], position[1])
        else:
            position = transformer2.transform(x4, y4)
            return Point(position[0], position[1])

def sweep_position(uwb_data: UwbDataPair, sweeped_anchor: UwbSingleData):
        # expand parameters
    try:
        anchor_A        = get_point_by_address(uwb_data.nearest.tag_address)
        anchor_B        = get_point_by_address(uwb_data.second.tag_address)
        ctrl_anchor     = get_point_by_address(sweeped_anchor.tag_address)
        distance_a      = uwb_data.nearest.distance
        distance_b      = uwb_data.second.distance
        distance_c      = sweeped_anchor.distance
        power_a         = uwb_data.nearest.power
        power_b         = uwb_data.second.power
    except AttributeError as err:
        return Point(0.0, 0.0, "-1 bad arguments")

    if anchor_A is None or anchor_B is None or ctrl_anchor is None:
        return Point(0.0, 0.0, "-2 wrong points received")

    transformer1 = Transformer.from_crs("EPSG:4326", "EPSG:2177")        #transform from WGS84 to PL-2000
    transformer2 = Transformer.from_crs("EPSG:2177", "EPSG:4326")        #transform from PL-2000 to WGS84
    anch_xy_A = transformer1.transform(anchor_A.x, anchor_A.y)
    anch_xy_B = transformer1.transform(anchor_B.x, anchor_B.y)
    ctrlanch_xy = transformer1.transform(ctrl_anchor.x, ctrl_anchor.y)
    scale_offset_factor = 1.005

    d = math.sqrt((anch_xy_B[0] - anch_xy_A[0]) ** 2 + (anch_xy_B[1] - anch_xy_A[1]) ** 2)

    # non intersecting
    if d > distance_a + distance_b:
        while (distance_a + distance_b < d and scale_offset_factor < MAX_UWB_OFFSET_FACTOR):
            if power_a < power_b:
                distance_b *= scale_offset_factor
            elif power_a > power_b:
                distance_a *= scale_offset_factor
            scale_offset_factor += 0.005
    if d > distance_a + distance_b:
        return Point(0, 0, "-2 non-intersecting")
    # One circle within other
    if d < abs(distance_a - distance_b):
        return Point(0, 0, "-3 one circle within other")
    # coincident circles
    if d == 0 and distance_a == distance_b:
        return Point(0, 0, "-4 coincident circles")
    else:
        a = (distance_a ** 2 - distance_b ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(distance_a ** 2 - a ** 2)
        x2 = anch_xy_A[0] + a * (anch_xy_B[0] - anch_xy_A[0]) / d
        y2 = anch_xy_A[1] + a * (anch_xy_B[1] - anch_xy_A[1]) / d
        x3 = x2 + h * (anch_xy_B[1] - anch_xy_A[1]) / d
        y3 = y2 - h * (anch_xy_B[0] - anch_xy_A[0]) / d

        x4 = x2 - h * (anch_xy_B[1] - anch_xy_A[1]) / d
        y4 = y2 + h * (anch_xy_B[0] - anch_xy_A[0]) / d

        #return (x3, y3, x4, y4)
        pa = (x3, y3)
        pb = (x4, y4)
        d1 = math.sqrt((ctrlanch_xy[0] - pa[0]) **2 + (ctrlanch_xy[1] - pa[1]) **2)
        d2 = math.sqrt((ctrlanch_xy[0] - pb[0]) **2 + (ctrlanch_xy[1] - pb[1]) **2)
        if abs(d1 - distance_c) < abs(d2 - distance_c):
            position = transformer2.transform(x3, y3)
            return Point(position[0], position[1])
        else:
            position = transformer2.transform(x4, y4)
            return Point(position[0], position[1])

def nmea_sentence_to_gps_point(data):
    """
    Converts GPS sentence in NMEA-2000 standard
    to instance of Point class
    """
    # DDMM.MMMM
    lat_raw = data[2]
    lat_deg = float(lat_raw[0:2])
    lat_min = float(lat_raw[2:])
    lat = lat_deg + (lat_min / 60)
    sign_lat = data[3]
    if sign_lat == "S":
        lat *= -1

    # DDDMM.MMMM
    long_raw = data[4]
    long_deg = float(long_raw[0:3])
    long_min = float(long_raw[3:])
    long = long_deg + (long_min / 60)
    long_sign = data[5]
    if long_sign == "W":
        long *= -1

    return GpsData(lat, long)


def get_gps_position(gps_serial: Serial, queue: Queue) -> Point:
    """
    Reads point from GPS device.
    """
    while (True):

        try:
            line = str(gps_serial.readline(), encoding="ASCII")
            if "GPGGA" in line: # read line containig position
                data = line.split(',')
                with open("gps_data.txt", "a+") as file:
                    file.write(line)
                if (int(data[7]) < 0):
                    continue# not enough satellites
                if queue.qsize()>6:
                    queue.get()
                queue.put(nmea_sentence_to_gps_point(data))
            else:
                with open("gps_data.txt", "a+") as file:
                    file.write("NO GPS SIGNAL\n")
        except(UnicodeDecodeError):
            pass

def mock_gps_position(queue: Queue, timer) -> Point:
    """
    Simulates GPS signal
    """
    while (True):
            point = GpsData(50.0, 18.0)
            point.x += timer.value * 0.1
            timer.value += 1
            if timer.value > 30:
                timer.value = 0
            queue.put(point)
            time.sleep(0.15)

def read_json_file():
    f = open("/home/wojtek/pbl/pbl-ford-ka/GPSdata.json")
    return json.load(f)

def load_points_from_json():
    points = []
    for line in read_json_file():
        points.append(Point(line['x'], line['y'], line ['address']))
    return points

def get_points():
    return load_points_from_json()

def get_point_by_address(address):
    for point in get_points():
        if point.address == address:
            return point
    return None

def get_point_tuple_from_UwbDataPair(pair: UwbDataPair):
    address_a = pair.nearest.tag_address
    address_b = pair.second.tag_address
    point_tuple = (get_point_by_address(address_a), get_point_by_address(address_b))
    return point_tuple