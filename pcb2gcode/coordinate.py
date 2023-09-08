from numpy import array

class Coordinate:
    """
    Helper object to store coordinates which could be visited
    to be later rendered using different offset and scale.
    """
    def __init__(self, x: int, y: int):
        """ Construct using int """
        self.x = x
        self.y = y

    def __array__(self):
        """ @return a numpy array using the base unit conversion """
        return array([self.x.base, self.y.base])
