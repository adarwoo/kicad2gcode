# Cutting tools for the CNC
from enum import IntEnu; 

class CuttingTool:
    class CutDir(IntEnum):
        UNKWOWN,
        UP,
        DOWN,
        UPDOWN

    class Geometry(IntEnum):
        ANGLED,
        FLAT
        
    def __new__(cls, *args, **kwargs):
        print("Creating instance of", cls.__name__)
        return super().__new__(cls)

    def __init__(self, diameter):
        self.type = __cls__.__name__
        self.diameter_um = 0
        self.tip_angle = 180
        self.cut_direction = CutDir
        self.rpm = 0
        self.z_feedrate = 0

class DrillBit(CuttingTool):
    pass

class RouterBit(CuttingTool):
    pass


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
