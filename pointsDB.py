from .mapping import Point
import json

def read_json_file():
    f = open("/home/wojtek/pbl/pbl-ford-ka/ros2_ws/src/gps/gps/GPSdata.json")
    return json.load(f)

def load_points_from_json():
    points = []
    for line in read_json_file():
        points.append(Point(line['x'], line['y'], line ['address']))
    return points

def getPoints(subset):
    if subset == 0:
        return [
            Point(50.290138, 18.677277, "AA:BB"),
            Point(50.289368, 18.678203, "CC:DD")]
    elif subset == 1:
        return load_points_from_json()
    else:
        return None

