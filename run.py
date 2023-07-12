from pbl_utils.spausyncing import Spausync

spausync = Spausync(family="AA", mock_ahrs=False, mock_gps=False)
#spausync2 = Spausync(family="BB")
spausync.launch()
#spausync2.launch()
while True:
    data = spausync.get_all_data()
    #data2 = spausync2.get_all_data()
    print("###FAMILY AA###")
    print(data)
    #print("###FAMILY BB###")
    #print(data2)
