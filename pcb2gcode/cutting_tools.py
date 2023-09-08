#!/usr/bin/env python3

# Cutting tools for the CNC
from enum import IntEnum
from logging import getLogger
from math import tan, radians

# pylint: disable=E0611 # The module is fully dynamic
from .config import global_settings as gs
# pylint: disable=E0611 # The module is fully dynamic
from .config import machining_data as md
# pylint: disable=E0611 # The module is fully dynamic
from .config import stock

from .utils import interpolate_lookup, round_significant
from .units import rpm, FeedRate, Unit, Length, degree


logger = getLogger(__name__)

# Multiple the diameter by this number to find the length of the tip of the bit
HEIGHT_TO_DIA_RATIO = tan(radians((180-gs.drillbit_point_angle())/2))

# Maximum depth allowed into the matyt board
MAX_DEPTH_ALLOWED = gs.backboard_thickness - gs.safe_distance - gs.exit_depth_min

# Compute the largest drillbit size where there is enough clearance in the backing board for
#  the point to exit cleanly
MAX_DRILLBIT_DIAMETER_FOR_CLEAN_EXIT = MAX_DEPTH_ALLOWED / HEIGHT_TO_DIA_RATIO


class CutDir(IntEnum):
    UNKWOWN = 0
    UP = 1
    DOWN = 2
    UPDOWN = 3


class CuttingTool:
    """Abstract base class for all cutting tools"""
    
    # Name of the stock in the config["stock"]
    __stockname__ = None
    
    # If True, allow for the tool to be larger than the specification
    allow_bigger = False
    
    # Order when sorted. Override to set the order during machining. Lowest go first.
    order = 0

    def __init__(self, diameter: Length, mfg_data):
        self.type = self.__class__
        self.diameter = diameter
        self.mfg_data = mfg_data
        self.tip_angle = gs.drillbit_point_angle
        self.cut_direction = CutDir.UNKWOWN
        self.rpm = rpm(0)
        self.z_feedrate = FeedRate.from_scalar(0)
        # If True, allow for larger sizes. OK for a drillbit, but not for a routerbit
        self.allow_bigger=False

        # Grab a set of interpolated data
        key_unit = Unit.get_unit(self.mfg_data.units[0])
        scalar_value = self.diameter(key_unit)
        self.interpolated_data = interpolate_lookup(self.mfg_data.data, scalar_value)
        
    def __eq__(self, other):
        return self.type is other.type and self.diameter == other.diameter
    
    def __lt__(self, other):
        """Override to allow sorting cutting tools by type and order"""
        if self.__class__.order == other.__class__.order:
            return self.diameter < other.diameter
        
        return self.__class__.order < other.__class__.order

    def interpolate(self, what):
        """ Using the manufactuing table and the diameter, interpolate a data """
        index = self.mfg_data.fields[1].index(what)
        unit = Unit.get_unit(self.mfg_data.units[1][index])
        return unit(round_significant(self.interpolated_data[index]))

    @classmethod
    def get_from_stock(cls, diameter):
        """
        Grab a stock object which is the closest to the required size
        The selection will involve the configuration
        @return A stock item object or None if no items could be matched
        """
        v = min_so_far = diameter
        nearest_diameter = None

        # Start with the largest bit - rational : A bigger hole will accomodate the part
        # In most cases, the plating (0.035 nominal) will make the hole smaller in the end
        for s in reversed(sorted(stock.get(cls.__stockname__, []))):
            lower = v - ((v * gs.downsizing_allowance_percent) / 100)
            upper = v + ((v * gs.oversizing_allowance_percent) / 100)

            # Skip too large of a hole
            if cls.allow_bigger:
                if s > upper:
                    continue
            elif s > v:
                continue

            # Stop if too small - won't get better!
            if s < lower:
                break

            # Whole size is ok, promote if difference is less
            if abs(v-s) < min_so_far:
                min_so_far = abs(v-s)

                if min_so_far == 0:
                    nearest_diameter = s
                    break

                nearest_diameter = s

        return cls(nearest_diameter) if nearest_diameter else None

    @classmethod
    def get_stock_size_range(cls):
        """
        @return The min-max range of the stock cutter sizes in Length
        """
        thestock = sorted(stock.get(cls.__stockname__,[]))
        return (thestock[0], thestock[-1])

    def get_nearest_stock_size(self):
        """
        Return the nearest stock size item or None
        """
        return self.get_from_stock(self.diameter)

    @staticmethod
    def request(cutting_tool):
        """
        Requests a cutting tool from the standard size
        May return a routerbit for drilling holes if that's the only option
        """
        # Normalize the cutting tool size matching sizes from our stock
        normalized_size_tool = cutting_tool.get_nearest_stock_size()

        def route_holes(cutting_tool = cutting_tool):
            # Use the contour router if not too big
            if gs.router_diameter_for_contour <= cutting_tool.diameter:
                return RouterBit(gs.router_diameter_for_contour)

            # Pick the stock bit
            normalized_size_tool = RouterBit(cutting_tool.diameter).get_nearest_stock_size()

            if normalized_size_tool:
                return normalized_size_tool

            # No suitable router bit found - Game over
            logger.error(
                "No suitable routerbit exits in the stock to cut a hole of %s.",
                cutting_tool.diameter
            )

            return None

        if normalized_size_tool is None:
            if cutting_tool.diameter < cutting_tool.get_stock_size_range()[0]:
                # Size is too small and not supported
                logger.warning(
                    "Cutting tool size: %s is too small", cutting_tool.diameter
                )
                
                return None

            # Else - it is too big
            if cutting_tool.diameter > cutting_tool.get_stock_size_range()[1]:
                if cutting_tool.type is RouterBit:
                    # Size is too large
                    logger.error(
                        "Cutting tool size: %s exceed largest stock bit",
                        cutting_tool.diameter
                    )
                    
                    return None
                else:
                    logger.info(
                        "Cutting tool size: %s exceed largest bit and will be routed",
                        cutting_tool.diameter
                    )
                    
                    return route_holes()

            # Else, it is not matched (tolerances and too tight)
            if cutting_tool.type is RouterBit:
                logger.error(
                    "No suitable routerbit found for this size: %s", cutting_tool.diameter
                )
                logger.info("Consider increasing over and under size tolerances")

            # Try to route it!
            return route_holes()

        # Make sure the bit geometry is compatible with the backing board thickness
        if normalized_size_tool.diameter > MAX_DRILLBIT_DIAMETER_FOR_CLEAN_EXIT:
            # If not found or too deep - the hole must be routed
            # - but let's drill the largest hole first
            # But to do so - since the router dia can be any smaller size
            # - we need to wait for the drill rack to be completed
            exit_depth_required = \
                gs.exit_depth_min + HEIGHT_TO_DIA_RATIO * normalized_size_tool.diameter

            logger.warning(
                "Exit depth required %s is greater than the max depth allowed %s\n"
                "Switching to routing", exit_depth_required, MAX_DEPTH_ALLOWED
            )

            return route_holes(normalized_size_tool)

        return normalized_size_tool

    def __hash__(self) -> int:
        return self.diameter.__hash__()


class DrillBit(CuttingTool):
    __stockname__ = "drillbits"
    order = 1

    def __init__(self, diameter):
        super().__init__(diameter, md.drillbits)
        self.cut_direction = CutDir.UP
        self.allow_bigger = True

        self.rpm = self.interpolate("speed")
        self.z_feedrate = self.interpolate("z_feed")

    def __repr__(self) -> str:
        return f"{self.diameter} {self.rpm} zfeed:{self.z_feedrate}"


class RouterBit(CuttingTool):
    __stockname__ = "routerbits"
    order = 2

    def __init__(self, diameter):
        super().__init__(diameter, md.routerbits)
        self.cut_direction = CutDir.UPDOWN

        self.rpm = self.interpolate("speed")
        self.z_feedrate = self.interpolate("z_feed")
        self.table_feed = self.interpolate("table_feed")
        self.exit_depth = self.interpolate("exit_depth")
        self.tip_angle = 180*degree

    def __repr__(self) -> str:
        return f"{self.diameter} {self.rpm} zfeed:{self.z_feedrate} feed:{self.table_feed}"

    def __hash__(self) -> int:
        # Negate for router bits
        return -abs(super().__hash__())
