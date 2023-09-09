# -*- coding: utf-8 -*-

#
# This file is part of the pcb2gcode distribution (https://github.com/adarwoo/pcb2gcode).
# Copyright (c) 2023 Guillaume ARRECKX (software@arreckx.com).
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
"""
Defines cutting tools objects as a hierachy for absreact handling
"""

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
    """ A Enum type to store the type of cut of a cutting tool. """
    UNKWOWN = 0 # Not known
    UP = 1      # Upcut. Chips are drawn upwards. Fine for drilling.
    DOWN = 2    # Pushes the shavings down
    UPDOWN = 3  # Also known as compression bit


class CuttingTool:
    """Abstract base class for all cutting tools"""

    # Name of the stock in the config["stock"]
    __stockname__ = None

    # If True, allow for the tool to be larger than the specification
    __allow_oversizing__ = False

    # Points the manufacturing data for the tool
    __mfg_data__ = None

    # __order__ when sorted. Override to set the __order__ during machining. Lowest go first.
    __order__ = 0

    def __init__(self, diameter: Length):
        self.type = self.__class__
        self.diameter = diameter
        self.tip_angle = gs.drillbit_point_angle
        self.cut_direction = CutDir.UNKWOWN
        self.rpm = rpm(0)
        self.z_feedrate = FeedRate.from_scalar(0)
        # If True, allow for larger sizes. OK for a drillbit, but not for a routerbit
        self.__allow_oversizing__=False

        # Grab a set of interpolated data
        key_unit = Unit.get_unit(self.__mfg_data__.units[0])
        scalar_value = self.diameter(key_unit)
        self.interpolated_data = interpolate_lookup(
            self.__class__.__mfg_data__.data, scalar_value)

    def __eq__(self, other):
        return self.type is other.type and self.diameter == other.diameter

    def __lt__(self, other):
        """Override to allow sorting cutting tools by type and __order__"""
        if self.__class__.__order__ == other.__class__.__order__:
            return self.diameter < other.diameter

        return self.__class__.__order__ < other.__class__.__order__

    def interpolate(self, what):
        """ Using the manufactuing table and the diameter, interpolate a data """
        index = self.__class__.__mfg_data__.fields[1].index(what)
        unit = Unit.get_unit(self.__class__.__mfg_data__.units[1][index])
        return unit(round_significant(self.interpolated_data[index]))

    @classmethod
    def get_from_stock(cls, diameter):
        """
        Grab a stock object which is the closest to the required size
        The selection will involve the configuration
        @return A stock item object or None if no items could be matched
        """
        variation = min_so_far = diameter
        nearest_diameter = None

        # Start with the largest bit - rational : A bigger hole will accomodate the part
        # In most cases, the plating (0.035 nominal) will make the hole smaller in the end
        for stock_size in reversed(sorted(stock.get(cls.__stockname__, []))):
            lower = variation - ((variation * gs.downsizing_allowance_percent) / 100)
            upper = variation + ((variation * gs.oversizing_allowance_percent) / 100)

            # Skip too large of a hole
            if cls.__allow_oversizing__:
                if stock_size > upper:
                    continue
            elif stock_size > variation:
                continue

            # Stop if too small - won't get better!
            if stock_size < lower:
                break

            # Whole size is ok, promote if difference is less
            if abs(variation-stock_size) < min_so_far:
                min_so_far = abs(variation-stock_size)

                if min_so_far == 0:
                    nearest_diameter = stock_size
                    break

                nearest_diameter = stock_size

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
    """ A drillbit cutter """
    __stockname__ = "drillbits"
    __order__ = 1
    __mfg_data__ = md.drillbits

    def __init__(self, diameter):
        super().__init__(diameter)
        self.cut_direction = CutDir.UP
        self.__allow_oversizing__ = True

        self.rpm = self.interpolate("speed")
        self.z_feedrate = self.interpolate("z_feed")

    def __repr__(self) -> str:
        return f"{self.diameter} {self.rpm} zfeed:{self.z_feedrate}"


class RouterBit(CuttingTool):
    """ A routerbit cutter """
    __stockname__ = "routerbits"
    __order__ = 2
    __mfg_data__ = md.routerbits

    def __init__(self, diameter):
        super().__init__(diameter)
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
