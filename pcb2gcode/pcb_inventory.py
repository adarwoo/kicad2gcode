#!/usr/bin/python3
import re

from math import tan, cos, sin, radians
from typing import List, Tuple
from .units import um, degree
from .utils import Coordinate

from numpy import array

class Feature:
    @classmethod
    @property
    def type(cls):
        return cls

class Hole(Feature):
    """
    Representation of a Hole information collected from KiCAD
    All dimensions shall be given as Length objects
    """
    def __init__(self, d, x, y, pth=True):
        self.x = x
        self.y = y
        self.pth = pth
        self.diameter = d

        # To be added by the machining
        self.tool_id = 0

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"{self.diameter} ({self.x}, {self.y})"


class Oblong(Hole):
    """ Representation of a oblong hole information collected from KiCAD """
    def __init__(self, d, x1, y1, x2, y2, pth=True):
        from math import sqrt

        super().__init__(d, x1, y1, pth)
        self.x2=x2
        self.y2=y2

        # The distance is used to determine if 2 holes are required / and / or routing is required
        self.distance=sqrt((self.x-self.x2)**2 + (self.y-self.y2)**2)

    def __str__(self):
        return "O" + super().__str__()


class Route(Feature):
    pass


class Inventory:
    """
    Create an inventory of Features which will require some machine.
    The inventory is created from the PCB data and does not factor how it will be machined
    """
    def __init__(self):
        self.pth = {} # type: Dict[Length, Feature]
        self.npth = {} # type: Dict[Length, Feature]

        # Work out the offset
        self.offset = board.GetDesignSettings().GetAuxOrigin()

    def _add_hole(self, hole: Hole, pth):
        if pth:
            self.pth_holes[hole.diameter] = hole
        else:
            self.npth_holes[hole.diameter] = hole

    def add_hole(self, pos_x, pos_y, size_x, size_y, orient, pth):
        """
        Add a hole to the inventory

        @param pos_x, pos_y Position of the hole in KiCad coordinate values
        @param size_x, size_y Size of the hole. Oblong hole have different sizes
        @param orient Orientation of the hole
        """
        pos = Coordinate(um(pos_x), -um(pos_y))

        if size_x == size_y:
            self._add_hole(
                Hole(um(size_x), pos),
                pth
            )
        else:
            orientation = degree(orient)

            # Determine the orientation
            # WARNING : As KiCad uses screen coordinates, angles are inverted
            hole_width = min(size_x, size_y)
            radius = (max(size_x, size_y) - hole_width) / 2
            angle = radians((90 if size_x < size_y else 0) - orient)
            dx = radius * cos(angle)
            dy = radius * sin(angle)
            x1, y1 = (pos[0] + dx, pos[1] + dy)
            x2, y2 = (pos[0] - dx, pos[1] - dy)

            # Append an oblong hole
            self._add_holes(
                Oblong(
                    um(hole_width),
                    Coordinate(um(x1), um(y1)),
                    Coordinate(um(x2), um(y2))
                ),
                pth
            )
