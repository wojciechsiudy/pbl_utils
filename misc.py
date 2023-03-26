from time import time

from .uwb_constants import UwbConstants

class StampedData:
    """
    Basic holder for synchronized data
    """
    def __init__(self):
        self.time_stamp = time()
        self.max_age = UwbConstants().get_value("MAX_DATA_AGE")

    def validate_age(self):
        """
        Function validating if recived data is not outdated
        """
        now = time()
        if now - self.time_stamp > self.max_age:
            return False
        else:
            return True
    

