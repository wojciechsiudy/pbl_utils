import BLE_GATT
import esptool
from time import time
from serial import Serial, SerialException
from .uwb_constants import UwbConstants
from .misc import StampedData
from multiprocessing import Process, Queue
UWB_ERROR_MESSAGE = "Hello Wojtek"
UWB_TIMEOUT_MESSAGE = "Timed out!"

class UwbDataError(Exception):
    pass

class ConnectionError(Exception):
    pass

class UwbFatalError(Exception):
    pass

class UwbIncorrectData(Exception):
    pass

class UwbData(StampedData):
    """
    Data returned from UWB device
    """
    def __init__(self, tag_adress:str = "none", distance:float = 0.0, 
                power:float = 0.0, valid:bool = True):
        super().__init__()
        self.tag_address = tag_adress
        self.distance = distance
        self.power = power
        self.valid = valid

    def __repr__(self) -> str:
        repr =  str(self.tag_address) + ' '
        repr += str(self.distance) + ' '
        repr += str(self.power) + ' '
        if self.valid:
            repr += "valid"
        else:
            repr += "invalid"
        return repr

    @staticmethod
    def create_UWB_data(data: str = ""):
        """
        Method converting raw UWB data to UwbData object
        
        WARNING!
        this method uses single-anchor format from spgh-2.0 or less
        """
        data_array = data.split("|")
        try:
            if len(data_array) < 2:
                raise UwbDataError
            if data_array[1] == UWB_TIMEOUT_MESSAGE:
                return UwbData(valid = False)
            tag_address = data_array[0][:5]
            distance = float(data_array[1])
            power = float(data_array[2])
        except ValueError:
            raise UwbDataError
        return UwbData(tag_address, distance, power)


class UwbDataPair:
    """
    Pair of UWB messages
    """
    def __init__(self, nearest: UwbData, second: UwbData):
        self.nearest = nearest
        self.second = second

    def __repr__(self) -> str:
        repr=f"Nearest: {self.nearest.__repr__()}\n Second: {self.second.__repr__()}\n"
        return repr
    
    @staticmethod
    def create_UWB_data_pair(data: str = ""):
        """
        Method converting raw UWB data to UwbDataPair object
        """
        datas = data.split("_")
        if len(datas) < 2:
            raise UwbDataError
        first_uwb = UwbData.create_UWB_data(datas[0])
        second_uwb = UwbData.create_UWB_data(datas[1])
        return UwbDataPair(first_uwb, second_uwb)


class UwbConnection:
    """
    Entity responsible for communication

    Usage:
        connection = UwbBluetoothConnection()
        connection.connect()
        connection.ask_for_distance(anchor_address)
        distance = connection.read_anwser()
        connection.disconnect()

    Constructor throws UwbFatalError when connection is
    not possible
    """
    def __init__(self):
        self.set_initial_values()
        self.read_settings_from_json()
        self.debug("Lanuching BLE device...", 2)
        self.measures_queue = Queue(maxsize=10)
        try:
            self.ble_device = BLE_GATT.Central(self.uwb_mac_adress)
            self.serial_device = Serial(self.settings.get_value("UWB_SERIAL_ADDRESS"), 
                                        baudrate=115200)
        except SerialException:
            self.debug("Serial error!", 1)
        except:
            self.debug("Bluetooth error. Device not found! Adress used: " + str(self.uwb_mac_adress), 0)
            # TODO: try connection again
            raise UwbFatalError
        self._set_processes()
        self._begin_process()

    def _set_processes(self):
        self.process_reader = Process(target=_uwb_anwser_serial_reader, 
                               args=(self.serial_device, self.measures_queue,))
    def _begin_process(self):
        self.process_reader.start()        

    def set_initial_values(self):
        self.last_address_nearest = "00:00"
        self.last_address_second = "00:00"
        self.last_reader_message=UwbDataPair(UwbData(),UwbData())
    def end(self):
        self.process_reader.terminate()    
    def read_settings_from_json(self):
        self.settings = UwbConstants()
        self.uwb_mac_adress = self.settings.get_value("DEVICE_ADDRESS")
        self.service_uuid = self.settings.get_value("SERVICE_UUID")
        self.read_characteristic = self.settings.get_value("READ_CHARACTERISTIC_UUID")
        self.write_characteristic = self.settings.get_value("WRITE_CHARACTERISTIC_UUID")
        self.debug_level = int(self.settings.get_value("DEBUG_LEVEL")) # type: ignore
        self.debug("Settings loaded!", 3)

    def debug(self, message: str, level=3):
        if self.debug_level >= level:
            print(message)

    def connect(self):
        self.debug("Connecting...", 2)
        try:
            self.ble_device.connect()
            #self.serial_device.open()
        except SerialException:
            self.debug("Serial error!", 1)
            raise ConnectionError
        except:
            self.debug("Connection failed. Some error in BLE-GATT", 1)
            raise ConnectionError
        self.debug("Device connected!", 2)
        
    def ask_for_distances(self, address_1: str, address_2: str):
        """
        Send ranging request to two anchors
        """
        if address_1 == self.last_address_nearest and address_2 == self.last_address_second:
            return # because request is not necessary
        self.last_address_nearest = address_1
        self.last_address_second = address_2
        message = address_1 + address_2
        open("log.txt", "a").write("\n" + message + "\n")
        self.debug("Sending to: " + address_1 + " and to: " + address_2, 3)
        try:
            self.ble_device.char_write(self.write_characteristic, bytes(message, 'utf-8'))
        except KeyError:
            self.debug("Write error. Probably UUID not found", 1)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError

    def get_last_UwbDataPair(self) -> UwbDataPair | None:
        try:
            if self.measures_queue.qsize() > 0:
                self.last_reader_message = UwbDataPair\
                    .create_UWB_data_pair(self.measures_queue.get())
            return self.last_reader_message
        except UwbDataError:
            self.debug("Wrong data recived. Probably message standard has changed.", 2)
            pass

    # def read_uwb_data(self, address: str) -> UwbDataPair:
    #     """
    #     Method provides distance to anchor that
    #     address is passed

    #     Throws:
    #         - UwbIncorrectData if tag is not avaliable
    #     """
    #     try:
    #         # t_ask=time.time()
    #         self.ask_for_distance(address)
    #         # t__read = time.time()
    #         # self.debug(f"Elapsed time in {self.ask_for_distance.__name__}: {str(t__read - t_ask)}", 2)
    #         uwb_data = self.get_last_UwbDataPair()
    #         # t_after = time.time()
    #         # self.debug(f"Elapsed time in {self.read_anwser.__name__}: {str(t_after - t__read)}", 2)
    #     except (ConnectionError, UwbDataError):
    #         self.debug("Connection failed", 2)
    #         self.restart()
    #         return 0
    #     if address != uwb_data.tag_address:
    #         self.debug("Old data or wrong tag anwsered.", 3)
    #         raise UwbIncorrectData
    #     elif uwb_data.tag_address is int:
    #         self.debug("!!!! Got address as an int. This error is not handled !!!!", 1)
    #         raise ConnectionError
    #     else:
    #         return uwb_data

    def disconnect(self):
        #self.ble_device.disconnect()
        #self.serial_device.close()
        pass

    def restart(self):
        self.disconnect()
        self.set_initial_values()
        serial_address = self.settings.get_value("UWB_SERIAL_ADDRESS")
        try:
            reset_commands = ["--port", serial_address, "run"]
            esptool.main(reset_commands)
        except SerialException:
            self.debug("Serial connection lost!", 1)
        self.connect()


def _uwb_anwser_serial_reader(serial_device: Serial, queue: Queue):
    """
    Read the last recived distance via serial

    Raw data is returnetd
    """
    while True:
        if queue.qsize() > 5:
                queue.get()
        try:
            data = str(serial_device.readline(), encoding="ASCII").strip()
            queue.put(data)
            open("log.txt", "a").write(str(time()) + "|" + data + "\n")
        except SerialException:
            print("Serial error during read.")
        