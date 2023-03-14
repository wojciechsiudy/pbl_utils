from geopy.distance import geodesic
from sys import argv
def display_info():
    print("Table of distances:")
    distances = [[0.0,0.0,0.0,0.0001],[0.0,0.0,0.0,0.00001],[0.0,0.0,0.0,0.000001],[0.0,0.0,0.0,0.0000001]]
    for distance in distances:
        print(f"Distance of {distance[3]} in degrees is equal to {geodesic((distance[0],distance[1]),(distance[2],distance[3])).m} in meters")
    print("To calculate distance between to points in meters please invoke:\n\
        python simple_distance.py <lat1> <lon1> <lat2> <lon2>")
def display_error():
    print("To print simple table with distances invoke without parameters")
    print("To calculate distance between to points in meters please invoke:\n\
        python simple_distance.py <lat1> <lon1> <lat2> <lon2>")
def calculate_distance(args : list[float]):
    assert len(args) == 4 and "There must be exactly 4 parameters"
    print(f"Distance between {args} is equal to {geodesic((args[0],args[1]),(args[2],args[3])).m} m")
if __name__=="__main__":
    if len(argv) == 1:
        display_info()
    elif len(argv) != 5:
        display_error()
    else:
        ar = argv.copy()
        ar.pop(0)
        calculate_distance(ar)