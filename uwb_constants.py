class UwbConstants:
    def __init__(self):
        self.settings = {
            "DEVICE_ADDRESS" : "90:84:2B:4A:3A:0C",
            "SERVICE_UUID" : "50218d18-bc42-11ed-afa1-0242ac120002",
            "READ_CHARACTERISTIC_UUID" : "57eb6e60-bc42-11ed-afa1-0242ac120002",
            "WRITE_CHARACTERISTIC_UUID" : "5b28fd72-bc42-11ed-afa1-0242ac120002",
            "DELAY_WRITE_CHARACTERISTIC_UUID" : "dbeea21d-446e-436c-97b0-0b450b615297",
            "UWB_SERIAL_ADDRESS": "/dev/UWB",
            "GPS_SERIAL_ADDRESS": "/dev/GPS",
            "MAX_RANGE_OFFSET_RATIO": "1.15",
            "DEBUG_LEVEL": "3"
        }

    def get_value(self, attribute_name):
        return self.settings.get(attribute_name)