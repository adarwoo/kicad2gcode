
class Coordinate:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


class DrillCoordinate(Coordinate):
    pass


class RouteVector:
    def __init__(self):
        pass

    def add_segment(start: Coordinate, end: Coordinate):
        pass

    def add_arc(start: Coordinate, end: Coordinate, center: Coordinate, diameter: int):
        pass
