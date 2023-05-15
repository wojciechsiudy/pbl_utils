from pbl_utils.spausyncing import Spausync

spausync = Spausync()
spausync.launch()
while True:
    data = spausync.get_all_data()
    print(data)