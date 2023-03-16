import json
import BLE_GATT
import esptool

from .uwb_constants import UwbConstants

UWB_ERROR_MESSAGE = "Hello Wojtek"

class UwbDataError(Exception):
    pass

class ConnectionError(Exception):
    pass

class UwbFatalError(Exception):
    pass

class UwbIncorrectData(Exception):
    pass

class UwbData:
    """
    Data returned from UWB device
    """
    def __init__(self, tag_adress:str = "none", distance:float = 0.0, power:float = 0.0):
        self.tag_address = tag_adress
        self.distance = distance
        self.power = power      

    @staticmethod
    def create_UWB_data(data: str = ""):
        """
        Method converting raw UWB data to UwbData object
        """
        data_array = data.split("|")
        if len(data_array) < 2:
            raise UwbDataError
        tag_address = data_array[0][:5]
        distance = float(data_array[1])
        power = float(data_array[2])
        return UwbData(tag_address, distance, power)



class UwbBluetoothConnection:
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
        self.debug_level = 3 # 0 is silent, 3 speaks a lot
        self.read_settings_from_json()
        self.debug("Lanuching BLE device...", 2)
        try:
            self.device = BLE_GATT.Central(self.uwb_mac_adress)
        except:
            self.debug("Device not found! Adress used: " + self.uwb_mac_adress, 0)
            raise UwbFatalError

    def read_settings_from_json(self):
        settings = UwbConstants()
        self.uwb_mac_adress = settings.get_value("DEVICE_ADDRESS")
        self.service_uuid = settings.get_value("SERVICE_UUID")
        self.read_characteristic = settings.get_value("READ_CHARACTERISTIC_UUID")
        self.write_characteristic = settings.get_value("WRITE_CHARACTERISTIC_UUID")
        self.debug("Settings loaded!", 3)

    def debug(self, message: str, level=3):
        if self.debug_level >= level:
            print(message)

    def connect(self):
        self.debug("Connecting...", 2)
        try:
            self.device.connect()
        except:
            self.debug("Connection failed. Some error in BLE-GATT", 1)
            raise ConnectionError
        self.debug("Device connected!", 2)

    def ask_for_distance(self, address: str, amount=1):
        """
        Send ranging request
        """
        message = address + str(amount)
        self.debug("Sending " + str(amount) + " packet(s) to " + address, 3)
        try:
            self.device.char_write(self.write_characteristic, bytes(message, 'utf-8'))
        except KeyError:
            self.debug("Write error. Probably UUID not found", 1)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError

    def read_anwser(self) -> UwbData:
        """
        Read the last recived distance
        """
        try:
            raw_anwser = self.device.char_read(self.read_characteristic)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError
        self.debug("Raw data is: " + str(raw_anwser), 4)
        anwser = ""
        for byte in raw_anwser:
            anwser += chr(byte)
        self.debug("Encoded data is: " + anwser, 3)
        if anwser == UWB_ERROR_MESSAGE:
            raise ConnectionError
        return UwbData.create_UWB_data(anwser)
    
    def read_uwb_data(self, address: str) -> UwbData:
        """
        Method provides distance to anchor that
        address is passed

        When any problem occurs connection is reset,
        however hard reset via RTS pin is not implemented

        Throws:
            - UwbIncorrectData if tag is not avaliable
        """
        try:
            self.ask_for_distance(address)
            uwb_data = self.read_anwser()
        except (ConnectionError, UwbDataError):
            self.debug("Connection failed", 2)
            self.restart()
            return 0
        if address != uwb_data.tag_address:
            self.debug("Old data or wrong tag anwsered.", 3)
            raise UwbIncorrectData
        elif uwb_data.distance is int:
            self.debug("!!!! Got distance as an int. This error is not handled !!!!", 1)
            raise ConnectionError
        else:
            return uwb_data


    def disconnect(self):
        self.device.disconnect()

    def restart(self):
        self.disconnect()
        self.connect()
