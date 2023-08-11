#!/usr/bin/python3
import re

from math import tan, cos, sin, radians
from typing import List, Tuple
import pcbnew

class Hole:
    """ Representation of a Hole information collected from KiCAD """
    def __init__(self, d, x, y, pth=True):
        self.x = x
        self.y = y
        self.pth = pth
        self.diameter = d

        # To be added by the machining
        self.tool_id = 0 # Type: complex

    def __repr__(self) -> str:
        return str(self)

    def __str__(self):
        return f"{MM(self.diameter):6.2f} ({MM(self.x):>8.2f}, {MM(self.y):<8.2f})"


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


class Inventory:
    """
    Create an inventory of items which will require some machine.
    The inventory is created from the PCB data and does not factor how it will be machined
    """
    def __init__(self, board):
        from pcbnew import PCB_VIA_T
        
        self.holes = list() # type: List[Hole]
        self.routing_segments = []

        # Start with the pads
        self.process_pads(board.GetPads())
        self.process_vias([t for t in board.GetTracks() if t.Type() == PCB_VIA_T])

        # Work out the offset
        self.offset = board.GetDesignSettings().GetAuxOrigin()

    def process_pads(self, pads):
        from pcbnew import PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH, PAD_DRILL_SHAPE_CIRCLE, \
        PAD_DRILL_SHAPE_OBLONG

        for pad in pads:
            # Check for pads where drilling or routing is required
            pad_attr = pad.GetAttribute()

            if pad_attr in [PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH]:
                pos = pad.GetPosition()
                size_x = pad.GetDrillSizeX()
                size_y = pad.GetDrillSizeY()
                
                # Drill or route?
                if (pad.GetDrillShape() == PAD_DRILL_SHAPE_CIRCLE) or (size_x == size_y):
                    self.holes.append(
                        Hole(pad.GetDrillSizeX(), pos[0], pos[1], pad_attr == PAD_ATTRIB_PTH)
                    )
                elif pad.GetDrillShape() == PAD_DRILL_SHAPE_OBLONG:
                    # Oblong pad location is the center
                    # X and Y sizes, with the orientation gives the start hole and end
                    orientation_degree = pad.GetOrientationDegrees()

                    # Determine the orientation
                    # WARNING : As KiCad uses screen coordinates, angles are inverted
                    hole_width = min(size_x, size_y)
                    radius = (max(size_x, size_y) - hole_width) / 2
                    angle = radians((90 if size_x < size_y else 0) - orientation_degree)
                    dx = radius * cos(angle)
                    dy = radius * sin(angle)
                    x1, y1 = (pos[0] + dx, pos[1] + dy)
                    x2, y2 = (pos[0] - dx, pos[1] - dy)

                    # Append an oblong hole
                    self.holes.append(
                        Oblong(hole_width, x1, y1, x2, y2, pad_attr == PAD_ATTRIB_PTH)
                    )

    def process_vias(self, vias):
        from pcbnew import VIATYPE_THROUGH

        for via in vias:
            hole_sz = via.GetDrillValue()

            # Must have a hole!
            if hole_sz == 0:
                continue

            if via.GetViaType() != VIATYPE_THROUGH:
                # We don't support burried vias
                continue

            # Check the via is through - discard other holes
            x, y = via.GetStart()

            self.holes.append(
                Hole(via.GetDrillValue(), x, y)
            )
