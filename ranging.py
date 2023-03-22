import json
import BLE_GATT
import esptool
import time
from serial import Serial, SerialException
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
        
        WARNING!
        this method uses single-anchor format from spgh-2.0 or less
        """
        data_array = data.split("|")
        if len(data_array) < 2:
            raise UwbDataError
        tag_address = data_array[0][:5]
        distance = float(data_array[1])
        power = float(data_array[2])
        return UwbData(tag_address, distance, power)

class UwbDataPair:
    """
    Pair of UWB messages
    """
    def __init__(self, nearest: UwbData, second: UwbData):
        self.nearest = nearest
        self.second = nearest

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
        self.debug_level = 3 # 0 is silent, 3 speaks a lot
        self.read_settings_from_json()
        self.debug("Lanuching BLE device...", 2)
        try:
            self.ble_device = BLE_GATT.Central(self.uwb_mac_adress)
            self.serial_device = Serial(self.settings.get_value("UWB_SERIAL_ADDRESS"), 
                                        baudrate=115200)
        except SerialException:
            self.debug("Serial error!", 1)
        except:
            self.debug("Bluetooth error. Device not found! Adress used: " + self.uwb_mac_adress, 0)
            raise UwbFatalError

    def read_settings_from_json(self):
        self.settings = UwbConstants()
        self.uwb_mac_adress = self.settings.get_value("DEVICE_ADDRESS")
        self.service_uuid = self.settings.get_value("SERVICE_UUID")
        self.read_characteristic = self.settings.get_value("READ_CHARACTERISTIC_UUID")
        self.write_characteristic = self.settings.get_value("WRITE_CHARACTERISTIC_UUID")
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

    @DeprecationWarning
    def ask_for_distance(self, address: str, amount=1):
        """
        Send ranging request
        """
        message = address + str(amount)
        self.debug("Sending " + str(amount) + " packet(s) to " + address, 3)
        try:
            t1=time.time()
            self.ble_device.char_write(self.write_characteristic, bytes(message, 'utf-8'))
            t2=time.time()
            self.debug(f"Elapsed time in {self.ble_device.char_write.__name__}: {str(t1 - t2)}", 2)

        except KeyError:
            self.debug("Write error. Probably UUID not found", 1)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError
        
    def ask_for_distances(self, address_1: str, address_2: str):
        """
        Send ranging request to two anchors
        """
        message = address_1 + address_2
        self.debug("Sending to: " + address_1 + " and to: " + address_2, 3)
        try:
            self.ble_device.char_write(self.write_characteristic, bytes(message, 'utf-8'))
        except KeyError:
            self.debug("Write error. Probably UUID not found", 1)
        except:
            self.debug("Unknown BLE error", 2)
            raise ConnectionError
        

    @DeprecationWarning
    def read_anwser_ble(self) -> UwbData:
        """
        Read the last recived distance via BLE
        """
        try:
            # t1=time.time()
            raw_anwser = self.ble_device.char_read(self.read_characteristic)
            # t2=time.time()
            # self.debug(f"Elapsed time in {self.read_anwser.__name__}: {str(t1 - t2)}", 2)

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
    
    def read_anwser_serial(self) -> UwbDataPair:
        """
        Read the last recived distance via serial
        """
        try:
            line = str(self.serial_device.readline(), encoding="ASCII")
            return UwbDataPair.create_UWB_data_pair(line)
        except SerialException:
            self.debug("Serial error during read.", 1)
            raise ConnectionError
        except UwbDataError:
            self.debug("Wrong data recived. Ignoring error.", 2)
            pass

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
            # t_ask=time.time()
            self.ask_for_distance(address)
            # t__read = time.time()
            # self.debug(f"Elapsed time in {self.ask_for_distance.__name__}: {str(t__read - t_ask)}", 2)
            uwb_data = self.read_anwser_serial()
            # t_after = time.time()
            # self.debug(f"Elapsed time in {self.read_anwser.__name__}: {str(t_after - t__read)}", 2)
        except (ConnectionError, UwbDataError):
            self.debug("Connection failed", 2)
            self.restart()
            return 0
        if address != uwb_data.tag_address:
            self.debug("Old data or wrong tag anwsered.", 3)
            raise UwbIncorrectData
        elif uwb_data.tag_address is int:
            self.debug("!!!! Got address as an int. This error is not handled !!!!", 1)
            raise ConnectionError
        else:
            return uwb_data


    def disconnect(self):
        #self.ble_device.disconnect()
        #self.serial_device.close()
        pass

    def restart(self):
        self.disconnect()
        serial_address = self.settings.get_value("UWB_SERIAL_ADDRESS")
        try:
            serial_test = Serial(serial_address)
            reset_commands = ["--port", serial_address, "run"]
            esptool.main(reset_commands)
        except SerialException:
            self.debug("Serial connection lost!", 1)
        self.connect()
