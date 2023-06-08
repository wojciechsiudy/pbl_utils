from .uwb_constants import UwbConstants

constants = UwbConstants()
print(constants.get_value("DEVICE_ADDRESS"))