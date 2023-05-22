from .spausyncing import SpauData
from .mapping import GpsData, Point
from .ranging import UwbDataPair,UwbData
from .inercing import AhrsData,InercialPoint
def process_file(filename:str):
    read_data = []
    with open(filename) as f:
        data = f.readlines()
    i = 0
    while i  < len(data):
        # validate DF
        if data[i+1].strip() != "True":
            i += 15
            continue
        
        # Time
        time = float(data[i+3].strip())
        
        # First UWB
        uwb_first_tag_address = data[i+5].strip().split(" ")[1]
        uwb_first_distance = float(data[i+5].strip().split(" ")[2])
        uwb_first_power = float(data[i+5].strip().split(" ")[3])
        uwb_first_is_valid = data[i+5].strip().split(" ")[4] == "valid"
        first_UwbData = UwbData(uwb_first_tag_address, uwb_first_distance, uwb_first_power, uwb_first_is_valid)
        # Second UWB
        uwb_second_tag_address = data[i+6].strip().split(" ")[1]
        uwb_second_distance = float(data[i+6].strip().split(" ")[2])
        uwb_second_power = float(data[i+6].strip().split(" ")[3])
        uwb_second_is_valid = data[i+6].strip().split(" ")[4] == "valid"
        second_UwbData = UwbData(uwb_second_tag_address, uwb_second_distance, uwb_second_power, uwb_second_is_valid)
        
        uwb_Data = UwbDataPair(first_UwbData, second_UwbData)
        
        # AHRS
        values = data[i+9].strip().split(" ")
        accel = InercialPoint(float(values[0]), float(values[1]), float(values[2]))
        gyro = InercialPoint(float(values[3]), float(values[4]), float(values[5]))
        mag = InercialPoint(float(values[6]), float(values[7]), float(values[8]))
        ahrs_Data = AhrsData(accel, gyro, mag)
        
        # GPS
        values = data[i+11].strip().split(" ")
        gps_Data = GpsData(float(values[0]), float(values[1]))
        
        # Calculated position
        values = data[i+13].strip().split(" ")
        x = float(values[1])
        y = float(values[2])
        adr_tag = values[3]
        position = Point(x, y, adr_tag)
        data = SpauData(uwb_Data, ahrs_Data, gps_Data, position)
        read_data.append(data)
        i += 15
    return read_data
if __name__ == "__main__":
    d = process_file("example_spaudata.txt")
    print(d)