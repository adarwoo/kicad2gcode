#
# Default cnstants used for the CNC
#
from utils import INTERPOLATE_LUT_AT
import uniontool

# Location of the rack description file in Yaml
RACK_FILE_PATH = "~/rack.yaml"

# Maximum allowed spindle speed RPM
MAX_SPINDLE_SPEED_RPM = 24000

# Minimum allowed spindle speed RPM
MIN_SPINDLE_SPEED = 10000

# Standard drill sizes in mm - Change to match own supplies
DRILLBIT_SIZES = uniontool.DRILLBIT_STANDARD_SIZES_MM

# Standard router bits in mm - Change to match own supplier
ROUTERBIT_SIZES = uniontool.ROUTERBIT_STANDARD_SIZES_MM

# Check the bit size is within the industry range
CHECK_WITHIN_DIAMETERS_ABSOLUTE_RANGE = lambda d: 0.05 <= d <= 6.4

# Max depth to drill into martyr board in mm
# Standard martyr/back/exit boards have typical thicknesses of 2mm to 3mm.
# We need to keep a safe distance from the machining plate!
# This may limit the max bit diameter usable, since the angled part of bit is longer and would
#  require to drill deeper to get a clear exit diameter, and go through the backboard
MAX_DEPTH_INTO_BACKBOARD = 1.5

# Minimum straight shaft exit depth in mm for all sizes (to add to the tip height)
MIN_EXIT_DEPTH = 0.7

# Geometry angle of the drill bit in degree
DRILLBIT_POINT_ANGLE = 135

# Drill speed in RPM
MAX_DRILLBIT_RPM = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.DRILLBIT_DATA_LOOKUP, 0)

# Max feed rate in mm/min
MAX_DRILLBIT_Z_FEEDRATE = lambda d: INTERPOLATE_LUT_AT(
    d, uniontool.DRILLBIT_DATA_LOOKUP, 1)

# Max Z feedrate for the CNC in mm/min
MAX_Z_FEEDRATE = 2000

# Min feedrate for the CNC in mm/min
MIN_Z_FEEDRATE = 200

# Maximum slot length to dia ratio for peck drilling before routing
# Example: If 4 - it means that the slot size (end to end) is 4xdiameter.
# For a 1mm bit, the max slot width is 4mm end-to-end  or 3mm center to center.
# Multiply by SLOT_DRILL_PER_HOLE_WIDTH to work out the number of pecks
# If 0 - a router bit will always be required to drill the slot
SLOT_DRILL_MAX_LENGTH_TO_DIAMETER_RATIO = 4

# Slot drilling pecking distance as ratio of the hole diameter
# So 1/4, means the pecking distance is 1/4 of the hole diameter
# A slot of 2 mm long, drill with a 1mm drill bit, will require 5 holes
SLOT_DRILL_PER_HOLE_WIDTH = 4

# Max oversize in % for a bit if no matching bit is found
# Example: 5 is 5% - so, the largest bit to drill a 1mm hole would be a 1.05mm bit and no more
MAX_OVERSIZING_PERCENT = 5

# Max downsizing for a bit
# Example: 5 is 5% - so, the smallest bit allowed to drill a 1mm hole would be a 0.95mm bit and no less
MAX_DOWNSIZING_PERCENT = 10

# Size of the router bit for routing the edges
EDGE_ROUTER_DIAMETER_MM = 1.6

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

# Now override the settings with custom values
from settings_overrides import *