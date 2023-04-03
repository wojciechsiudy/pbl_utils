from .ranging import UwbConnection, UwbData, _uwb_anwser_serial_reader
from multiprocessing import Process, Queue
from serial import Serial

class BearingConnection(UwbConnection):
    def ask_for_distances(self, address_1: str):
        message = address_1 + str(1)
        self.debug("Sending to: " + address_1, 3)
        try:
            self.ble_device.char_write(self.write_characteristic, bytes(message, 'utf-8'))
        except KeyError:
            self.debug("Write error. Probably UUID not found", 1)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError

class BearingUwb():
    def __init__(self):
        self.connections = [BearingConnection(), BearingConnection()]
    def end(self):
        for con in self.connections:
            con.end()
    def get_last_messages(self) -> tuple(UwbData,UwbData):
        return tuple( x.get_last_UwbDataPair() for x in self.connections)
        