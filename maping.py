import math
from serial import Serial

POSITION_RADIUS_M = float('inf')
MAX_UWB_OFFSET_FACTOR = 1.15


class Point:
    def __init__(self, x, y, address="TAG"):
        self.x = x
        self.y = y
        self.address = address
        self.is_observed = False

    def is_around(self, another):
        distance = self.get_distance_to(another)
        if (distance > POSITION_RADIUS_M):
            return False
        else:
            return True

    def get_distance_to(self, another):
        lat_1 = self.y
        lng_1 = self.x
        lat_2 = another.y
        lng_2 = another.x
        lng_1, lat_1, lng_2, lat_2 = map(math.radians, [lng_1, lat_1, lng_2, lat_2])
        d_lat = lat_2 - lat_1
        d_lng = lng_2 - lng_1
        temp = (
                math.sin(d_lat / 2) ** 2
                + math.cos(lat_1)
                * math.cos(lat_2)
                * math.sin(d_lng / 2) ** 2
        )
        return 1000 * 6373.0 * (2 * math.atan2(math.sqrt(temp), math.sqrt(1 - temp)))


from geopy.distance import geodesic


def calculate_position(anchor_A, anchor_B, ctrl_anchor, distance_a,
                       distance_b):  # anchor_A ze współrzędnymi "(0,0)", distance_a/b od anchorów
    try:
        # c = anchor_A.get_distance_to(anchor_B) #odległośc między anchorami
        pa = (anchor_A.x, anchor_A.y)
        pb = (anchor_B.x, anchor_B.y)
        c = geodesic(pa, pb).m
        scale_offset_factor = 1.0
        while (distance_a + distance_b < c and scale_offset_factor < MAX_UWB_OFFSET_FACTOR):
            scale_offset_factor += 1.005
            distance_a *= scale_offset_factor
            distance_b *= scale_offset_factor
        # print("C:", c)
        cos_a = (pow(distance_b, 2) + pow(c, 2) - pow(distance_a, 2)) / abs(2 * distance_b * c)
        # print("COS_A:",cos_a)
        tempy = float(((distance_b * cos_a) / 1852) / 60)
        tempx = float(((distance_b * math.sqrt(1 - cos_a * cos_a)) / 1852) / 60)
        # print("tempx:", tempx, "tempy:", tempy)
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


def gps_data_to_point(data):
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
    gps_serial = Serial("/dev/GPS")
    while (True):
        try:
            line = str(gps_serial.readline(), encoding="ASCII")
            if "GPGGA" in line:
                data = line.split(',')
                if (int(data[7]) > 0):  # enough satellites
                    return (gps_data_to_point(data))
        except(UnicodeDecodeError):
            pass
