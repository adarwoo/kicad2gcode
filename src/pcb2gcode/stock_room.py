#!/usr/bin/python3
from utils import interpolate_lookup
from config import config
from units import Quantity

# Defines the StockRoom class.
# This class defines a virtual stock room storing Consumables
# (stock with normal wear and tear) and fixtures.

# The stockroom is persisted in a Yaml file.
# The idea, is that the Yaml could be edited - but also persisted.

class StockItem:
    """
    The base class for all items stored in the stock room
    """
    def __init__(self, name, **kwargs):
        self.name=name
        self.conf=kwargs

# Types only
class Consumable(StockItem):
    pass

class Fixture(StockItem):
    pass


class CuttingTool(Consumable):
    def __init__(self, diameter: Quantity):
        self.diameter = diameter

    def __call__(self, target_unit=None):
        return self.diameter(target_unit)

    @property
    def max_rpm(self):
        return interpolate_lookup(config.drill_data, self(), 2)

    @property
    def max_z_feedrate(self):
        return interpolate_lookup(config.drill_data, 3)

# Return the recommended router RPM based on the diameter (mm)
ROUTERBIT_SPINDLE_SPEED_FROM_DIAMETER = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.ROUTERBIT_DATA_LOOKUP, 0)

# Return the Z feedrate of the router bit based on the diameter (mm)
# Note : This feedrate assumes optimum RPM. If the RPM is less, slow the feed proportionally.
ROUTERBIT_Z_FEEDRATE_FROM_DIAMETER = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.ROUTERBIT_DATA_LOOKUP, 2, 1000)

# Returns the table feedrate in mm/min of the router bit based on the diameter (mm)
# Note : This feedrate assumes optimum RPM. If the RPM is less, slow the feed proportionally.
ROUTERBIT_TABLE_FEEDRATE_FROM_DIAMETER = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.ROUTERBIT_DATA_LOOKUP, 1, 1000)

# Return the depth (mm) into the backing board required for the given bit diameter (mm)
ROUTERBIT_EXIT_DEPTH_FROM_DIAMETER = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.ROUTERBIT_DATA_LOOKUP, 3)
