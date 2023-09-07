#!/usr/bin/python3

# Provides the 'Machining' class which uses the Inventory to check
#  all machining aspects, like creating the rack and generating the GCode.
# Dimensions are kept as um until the GCode rendering
from enum import IntEnum

# Grab the setups
from .pcb_inventory import Inventory, Oblong, Hole, Route
from .rack import Rack
from .cutting_tools import DrillBit, RouterBit
from .config import global_settings as gs
from .operations import Operations

import logging


logger = logging.getLogger(__name__)


class Machining:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

        # Drill ops for each tool in the rack
        self.drill_ops = {} # type: list(int, DrillCoordinate)

    def create_tool_rack(self, ops: Operations):
        """
        Create a unique list of all the holes sizes
        """
        # Start with an unlimited rack
        rack = Rack()

        # Start with inspecting every holes to be made
        features = self.inventory.get_features(ops)
       
        for by_diameter in features.values():
            for feature in by_diameter:
                try:
                    # Oblong holes may require routing
                    if isinstance(feature, Oblong):
                        if feature.distance > feature.diameter * gs.max_length_to_bit_diameter:
                            rack.request(RouterBit(feature.diameter))
                        else:
                            rack.request(DrillBit(feature.diameter))
                    elif isinstance(feature, Hole):
                        rack.request(DrillBit(feature.diameter))
                    elif isinstance(feature, Route):
                        rack.request(RouterBit(feature.diameter))
                    else:
                        raise RuntimeError()
                except ValueError:
                    logger.error("No solution exist for a tool request")

        # Return the rack
        return rack

    def gcode(self, operation: Operations, rack: Rack):
        # Start with the drills

        # Grab the tools from the rack - sort by smallest to the largest
        pass
