import json
import BLE_GATT
import esptool

UWB_ERROR_MESSAGE = "Hello Dupa"

class UwbDataError(Exception):
    pass

class ConnectionError(Exception):
    pass

class UwbFatalError(Exception):
    pass

class UwbData:
    """
    Data returned from UWB device
    """
    def __init__(self, data: str = ""):
        data_array = data.split("|")
        if len(data_array) < 2:
            raise UwbDataError
        self.tag_address = data_array[0][:5]
        self.distance = float(data_array[1])
        self.power = float(data_array[2])

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
        self.debug_level = 0 # 0 is silent, 3 speaks a lot
        self.read_settings_from_json()
        self.debug("Lanuching BLE device...", 2)
        try:
            self.device = BLE_GATT.Central(self.uwb_mac_adress)
        except:
            self.debug("Device not found!", 0)
            raise UwbFatalError

    def read_settings_from_json(self):
        try:
            file = open("settings.json")
        except FileNotFoundError:
            self.debug("Settings file not found! Aborting setup.", 1)
            return
        settings = json.load(file)
        self.uwb_mac_adress = settings["DEVICE_ADDRESS"]
        self.service_uuid = settings["SERVICE_UUID"]
        self.read_characteristic = settings["READ_CHARACTERISTIC_UUID"]
        self.write_characteristic = settings["WRITE_CHARACTERISTIC_UUID"]
        self.debug("Settings loaded!", 3)

    def debug(self, message: str, level=3):
        if self.debug_level <= level:
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
        self.debug("Raw data is: " + str(raw_anwser), 3)
        anwser = ""
        for byte in raw_anwser:
            anwser += chr(byte)
        self.debug("Encoded data is: " + anwser, 3)
        if anwser == UWB_ERROR_MESSAGE:
            raise ConnectionError
        return UwbData(anwser)
    
    def tmp_get_distance(self, address: str) -> float:
        try:
            self.ask_for_distance(address)
            uwb_data = self.read_anwser()
        except (ConnectionError, UwbDataError):
            self.debug("Connection failed", 2)
            self.restart()
            return 0
        if address != uwb_data.tag_address:
            self.debug("Old data or wrong tag anwsered.", 3)
        return uwb_data.distance


    def disconnect(self):
        self.device.disconnect()

    def restart(self):
        self.disconnect()
        self.connect()


# sample to be deleted soon
try:
    connection = UwbBluetoothConnection()
except UwbFatalError:
    raise SystemExit
connection.connect()
connection.debug_level = 3


for i in range(3000):
    print(connection.tmp_get_distance("AA:04"))
    print(connection.tmp_get_distance("AA:05"))
