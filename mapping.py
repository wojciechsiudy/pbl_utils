import math
from serial import Serial
from geopy.distance import geodesic
from pyproj import Transformer

from .uwb_constants import UwbConstants

POSITION_RADIUS_M : float = float('inf')
MAX_UWB_OFFSET_FACTOR: float = 1.15


class Point:
    """
    Class holding data about point on Earth surface
    """
    def __init__(self, x: float, y: float , address:str="TAG"):
        self.x = x
        self.y = y
        self.address = address

    def is_around(self, another):
        distance = get_distance(self, another)
        if (distance > POSITION_RADIUS_M):
            return False
        else:
            return True

def get_distance(a:Point, b:Point) -> float:
    pa = (a.x, a.y)
    pb = (b.x, b.y)
    return geodesic(pa, pb).m

def calculate_position(anchor_A: Point, anchor_B: Point, ctrl_anchor: Point, 
                distance_a: float, distance_b: float, 
                power_a: float, power_b: float):
    """
    Function calculating position based on:
        - positions     of anchor_A and anchor_B
        - position      of ctrl_anchor from GPS
        - distances     to anchor_A and anchor_B    in meters
        - power         of anchor_A and anchor_B    in dB

    Using WGS-84 ellipsoid and EPSG2177
    """
    transformer1 = Transformer.from_crs("EPSG:4326", "EPSG:2177")        #transform from WGS84 to PL-2000
    transformer2 = Transformer.from_crs("EPSG:2177", "EPSG:4326")        #transform from PL-2000 to WGS84
    anch_xy_A = transformer1.transform(anchor_A.x, anchor_A.y)
    anch_xy_B = transformer1.transform(anchor_B.x, anchor_B.y)
    ctrlanch_xy = transformer1.transform(ctrl_anchor.x, ctrl_anchor.y)
    scale_offset_factor = 1.0
    
    d = math.sqrt((anch_xy_B[0] - anch_xy_A[0]) ** 2 + (anch_xy_B[1] - anch_xy_A[1]) ** 2)
    
    ra = distance_a
    rb = distance_b
    # non intersecting
    if d > ra + rb:
        while (ra + rb < d and scale_offset_factor < MAX_UWB_OFFSET_FACTOR):
            scale_offset_factor += 1.005
            if power_a>power_b:
                rb *= scale_offset_factor
            elif power_a<power_b:
                ra *= scale_offset_factor
    if d > ra + rb:
        return Point(0, 0)
    # One circle within other
    if d < abs(ra - rb):
        return Point(0, 0)
    # coincident circles
    if d == 0 and ra == rb:
        return Point(0, 0)
    else:
        a = (ra ** 2 - rb ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(ra ** 2 - a ** 2)
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


'''def calculate_position(anchor_A:Point, anchor_B:Point,\
    ctrl_anchor:Point, distance_a:float, distance_b:float):  # anchor_A ze współrzędnymi "(0,0)", distance_a/b od anchorów

    try:
        # c = anchor_A.get_distance_to(anchor_B) #odległośc między anchorami
        c = get_distance(anchor_A,anchor_B)
        scale_offset_factor = 1.0
        while (distance_a + distance_b < c and scale_offset_factor < MAX_UWB_OFFSET_FACTOR):
            scale_offset_factor += 1.005
            distance_a *= scale_offset_factor
            distance_b *= scale_offset_factor
        # print("C:", c)
        cos_a = (pow(distance_b, 2) + pow(c, 2) - pow(distance_a, 2)) / abs(2 * distance_b * c)
        #cos_a = (pow(distance_a, 2) + pow(distance_b, 2) - pow(c, 2)) / (2 * (distance_a * distance_b))
        print("COS_A:",cos_a)
        #tempy = float(((distance_b * cos_a) / 1852) / 60)
        tempy = float((distance_b * cos_a) / 111139)
        #tempx = float(((distance_b * math.sqrt(1 - cos_a * cos_a)) / 1852) / 60)
        tempx = float((distance_b * math.sqrt(1 - cos_a * cos_a)) / 111139)
        #print("tempx:", tempx, "tempy:", tempy)
        if anchor_A.x > ctrl_anchor.x:
            x = anchor_A.x - tempx
        else:
            x = anchor_A.x + tempx
        if anchor_A.y > ctrl_anchor.y:
            y = anchor_A.y - tempy
        else:
            y = anchor_A.y + tempy
    except (ZeroDivisionError, ValueError, AttributeError):
        return Point(0.0, 0.0)
    return Point(x, y)

def calc_circle(anchor_A, anchor_B, ctrl_anchor, distance_a, distance_b):
    # circle 1: (x0, y0), radius r0
    # circle 2: (x1, y1), radius r1

    d = math.sqrt((anchor_B.x - anchor_A.x) ** 2 + (anchor_B.y - anchor_A.y) ** 2)
    ra = distance_a/111139
    rb = distance_b/111139
    # non intersecting
    if d > ra + rb:
        return Point(0, 0)
    # One circle within other
    if d < abs(ra - rb):
        return Point(0, 0)
    # coincident circles
    if d == 0 and ra == rb:
        return Point(0, 0)
    else:
        a = (ra ** 2 - rb ** 2 + d ** 2) / (2 * d)
        h = math.sqrt(ra ** 2 - a ** 2)
        x2 = anchor_A.x + a * (anchor_B.x - anchor_A.x) / d
        y2 = anchor_A.y + a * (anchor_B.y - anchor_A.y) / d
        x3 = x2 + h * (anchor_B.y - anchor_A.y) / d
        y3 = y2 - h * (anchor_B.x - anchor_A.x) / d

        x4 = x2 - h * (anchor_B.y - anchor_A.y) / d
        y4 = y2 + h * (anchor_B.x - anchor_A.x) / d

        #return (x3, y3, x4, y4)
        pa = (x3, y3)
        pb = (x4, y4)
        pg = (ctrl_anchor.x, ctrl_anchor.y)
        if geodesic(pa, pg).m < geodesic(pb, pg).m:
            return Point(x3, y3)
        else:
            return Point(x4, y4)'''

def gps_data_to_point(data):
    """
    Converts GPS sentence in NMEA-2000 standard
    to instance of Point class
    """
    lat_raw = data[2]
    lat_deg = float(lat_raw[0:2])
    lat_min = float(lat_raw[2:])
    lat = lat_deg + (lat_min / 60)
    sign_lat = data[3]
    if sign_lat == "S":
        lat *= -1

    long_raw = data[4]
    long_deg = float(long_raw[0:3])
    long_min = float(long_raw[3:])
    long = long_deg + (long_min / 60)
    long_sign = data[5]
    if long_sign == "W":
        long *= -1

    return Point(lat, long)


def get_position():
    """
    Reads point from GPS device.
    """
    settings = UwbConstants()
    gps_serial = Serial(settings.get_value("GPS_SERIAL_ADDRESS"))
    while (True):
        try:
            line = str(gps_serial.readline(), encoding="ASCII")
            if "GPGGA" in line: # read line containig position
                data = line.split(',')
                if (int(data[7]) > 0):  # enough satellites
                    return (gps_data_to_point(data))
        except(UnicodeDecodeError):
            pass
