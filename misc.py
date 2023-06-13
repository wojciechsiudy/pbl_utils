from time import time

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
        max_age = 5.0
        now = time()
        if now - self.time_stamp > max_age:
            return False
        else:
            return True

def log(filename, message):
    """
    Function for logging
    """
    open(filename, "a+").write(message + "\n")
