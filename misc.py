from time import time

from .uwb_constants import UwbConstants

class StampedData:
    """
    Basic holder for synchronized data
    """
    def __init__(self):
        self.time_stamp = time()

    def validate_age(self):
        """
        Function validating if recived data is not outdated
        """
        settings = UwbConstants()
        max_age = settings.get_value("MAX_DATA_AGE")
        now = time()
        if now - self.time_stamp > max_age:
            return False
        else:
            return True
    

