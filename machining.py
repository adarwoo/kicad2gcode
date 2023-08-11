#!/usr/bin/python3

# Provides the 'Machining' class which uses the Inventory to check
#  all machining aspects, like creating the rack and generating the GCode.
# Dimensions are kept as um until the GCode rendering
from enum import IntEnum

# Grab the setups
from settings import SLOT_DRILL_MAX_LENGTH_TO_DIAMETER_RATIO

from inventory import Inventory, Oblong
from rack import Rack
from assets import *

import logging


logger = logging.getLogger(__name__)


class MachiningWhat(IntEnum):
    """ Used to tell the Machining class which holes to do """
    DRILL_PTH = 0b0001        # Includes routing oblongs
    DRILL_NPTH = 0b0010      # Includes routing oblongs
    ROUTE_OUTLINE = 0b0100
    DRILL_NPTH_AND_ROUTE_OUTLINE = DRILL_NPTH | ROUTE_OUTLINE
    DRILL_ALL = DRILL_PTH | DRILL_NPTH
    DRILL_AND_ROUTE_ALL = DRILL_ALL | ROUTE_OUTLINE


class Machining:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

        # Drill ops for each tool in the rack
        self.drill_ops = {} # type: list(int, DrillCoordinate)

    def create_tool_rack(self, operation: MachiningWhat):
        """
        Create a unique list of all the holes sizes
        """
        # Start with an unlimited rack
        rack = Rack()

        # Start with inspecting every holes to be made
        for h in self.inventory.holes:
            if (operation & MachiningWhat.DRILL_PTH and h.pth) or (operation & MachiningWhat.DRILL_NPTH and not h.pth):
                # Oblong holes may require routing
                if isinstance(h, Oblong):
                    if SLOT_DRILL_MAX_LENGTH_TO_DIAMETER_RATIO / h.distance < h.diameter:
                        rack.request(1j*h.diameter)
                    else:
                        rack.request(h.diameter)
                else:
                    rack.request(h.diameter)

        # Next - route the contours
        # TODO

        # Return the rack
        return rack

    def gcode(self, operation: MachiningWhat, rack: Rack):
        # Start with the drills

        # Grab the tools from the rack - sort by smallest to the largest
        pass
