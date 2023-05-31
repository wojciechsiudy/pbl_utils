import numpy as np
from typing import List,Tuple
from pbl_utils.mapping import Point


def getGPSposition(points:List[Point]) -> tuple[Point, float, float]:
    """ Function that picks the middle of given GPS points and calculates standard error
    
    Args:
        points (List[Point]): list of GPS points

    Returns:
        tuple[Point, float, float]: mean GPS point, standard deviation accros X axis and standard deviation across Y axis
    """
    x = np.array([p.x for p in points])
    y = np.array([p.y for p in points])
    pos = Point(np.mean(x),np.mean(y))
    return (pos, np.std(x),np.std(y))

if __name__ == "__main__":
    import random
    l = [Point(2.0 + random.random()-0.5,1.0+random.random()-0.5) for x in range(50)]
    print(l)
    print(getGPSposition(l))