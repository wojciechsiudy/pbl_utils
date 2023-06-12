from pbl_utils.mapping import GpsData, Point, sweep_position, get_point_by_address, calculate_position
from pbl_utils.ranging import UwbDataPair,UwbSingleData
from pbl_utils.inercing import AhrsData,InercialPoint
from pbl_utils.spausyncing import SpauData

import matplotlib.pyplot as plt

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
        first_UwbData = UwbSingleData(uwb_first_tag_address, uwb_first_distance, uwb_first_power, uwb_first_is_valid)
        # Second UWB
        uwb_second_tag_address = data[i+6].strip().split(" ")[1]
        uwb_second_distance = float(data[i+6].strip().split(" ")[2])
        uwb_second_power = float(data[i+6].strip().split(" ")[3])
        uwb_second_is_valid = data[i+6].strip().split(" ")[4] == "valid"
        second_UwbData = UwbSingleData(uwb_second_tag_address, uwb_second_distance, uwb_second_power, uwb_second_is_valid)

        uwb_Data = UwbDataPair(first_UwbData, second_UwbData)

        # AHRS
        values = data[i+9].strip().split(", ")
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
        y = float(values[3])
        adr_tag = values[5]
        position = Point(x, y, adr_tag)
        data_output = SpauData(uwb_Data, ahrs_Data, gps_Data, position, time)
        read_data.append(data_output)
        i += 15
    return read_data

class Sweep():
    def __init__(self, time, sweeps):
        self.time = time
        self.sweeps = sweeps

def parse_sweep_line(line:str):
    if "_" in line:
        return ("Timed out!", 0, 0)

    index = 0
    time = ""

    curr_character = ""

    try:
        while curr_character != ":":
            time += curr_character
            curr_character = line[index]
            index += 1

        while curr_character != "|":
            curr_character = line[index]
            index += 1

        data = line[index:].split("|")

        if "Timed out!" in data:
            return ("Timed out!", 0, 0)

        address = data[0]
        range = data[1]
        power = data[2]

    except IndexError:
        return ("Timed out!", 0, 0)

    return (address, range, power)


def process_sweep(filename):
    sweeps = []
    sweep = []
    with open(filename) as f:
        was_sweep = False
        for line in f.readlines():
            data_all = line.split(":")
            if "SWEEP" in line:
                if was_sweep == False:
                    was_sweep = True
                    time = data_all[0]
                else:
                    sweeps.append(Sweep(time, sweep))
                    sweep = []
                    was_sweep = False
            single_sweep = parse_sweep_line(line)
            if single_sweep[0] == "Timed out!":
                continue
            else:
                sweep.append(single_sweep)

    return sweeps



if __name__ == "__main__":
    gps_x = []
    gps_y = []
    calc_x = []
    calc_y = []

    sweeps = process_sweep("seria2_ranging_log.txt")
    data = process_file("seria2_data.txt")
    #print(data)

    # with open("calculated_positions.csv", "w") as f:
    #     for d in data:
    #         f.write(str(d.calculated_position.x) + "," + str(d.calculated_position.y) + "\n")

    for d in data:
        for s in sweeps:
            #print(s.sweeps)
            if abs(float(s.time) - d.time) < 1.5:
                if (len(s.sweeps) > 2):
                    anchor_a = get_point_by_address(d.uwb_data_pair.nearest.tag_address)
                    anchor_b = get_point_by_address(d.uwb_data_pair.second.tag_address)
                    distance_a = float(d.uwb_data_pair.nearest.distance)
                    distance_b = float(d.uwb_data_pair.second.distance)
                    distance_c = float(s.sweeps[2][1])
                    power_a = float(d.uwb_data_pair.nearest.power)
                    power_b = float(d.uwb_data_pair.second.power)
                    ctr_anchor = get_point_by_address(s.sweeps[2][0])
                    if anchor_a is not None and anchor_b is not None and ctr_anchor is not None:
                        sweep = sweep_position(anchor_a, anchor_b, ctr_anchor, distance_a, distance_b, distance_c, power_a, power_b)
                        position = calculate_position(GpsData(ctr_anchor.x, ctr_anchor.y),
                                                      UwbDataPair(UwbSingleData(d.uwb_data_pair.nearest.tag_address, distance_a, power_a, True),
                                                                  UwbSingleData(d.uwb_data_pair.second.tag_address, distance_b, power_b, True)),
                                                    (anchor_a, anchor_b))
                        calc_x.append(position.x)
                        calc_y.append(position.y)
                        print(position.x, position.y)
                    break


        # if d.calculated_position.x == 0.0 or d.calculated_position.y == 0.0 or d.gps_data.y == 0.0 or d.gps_data.x == 0.0:
        #     continue
        # else:
        #     gps_x.append(d.gps_data.x)
        #     gps_y.append(d.gps_data.y)
        #     calc_x.append(d.calculated_position.x)
        #     calc_y.append(d.calculated_position.y)

    #make the plot
    #plt.plot(gps_y, gps_x, 'ro')
    plt.plot(calc_y, calc_x, 'bo')
    #plt.plot(anchors_y, anchors_x, 'gs')

    plt.show()
