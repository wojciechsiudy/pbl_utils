class UwbConstants:
    def __init__(self):
        self.settings = {
            "DEVICE_ADDRESS" : "30:C6:F7:3A:69:EA",
            "SERVICE_UUID" : "50218d18-bc42-11ed-afa1-0242ac120002",
            "READ_CHARACTERISTIC_UUID" : "57eb6e60-bc42-11ed-afa1-0242ac120002",
            "WRITE_CHARACTERISTIC_UUID" : "5b28fd72-bc42-11ed-afa1-0242ac120002",
            "UWB_SERIAL_ADDRESS": "/dev/UWB",
            "MAX_RANGE_OFFSET_RATIO": "1.15"
        }

    def get_value(self, attribute_name):
        return self.settings.get(attribute_name)