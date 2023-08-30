#!/usr/bin/env python3

# Cutting tools for the CNC
from enum import IntEnum
from config import config
from utils import interpolate_lookup, round_significant
import units


class CutDir(IntEnum):
    UNKWOWN = 0
    UP = 1
    DOWN = 2
    UPDOWN = 3


class CuttingTool:
    __stock__ = []

    def __init__(self, diameter, mfg_data):
        self.type = __class__.__name__
        self.diameter = diameter
        self.mfg_data = mfg_data
        self.tip_angle = config.gs.drillbit_point_angle
        self.cut_direction = CutDir.UNKWOWN
        self.rpm = units.rpm(0)
        self.z_feedrate = units.FeedRate.from_scalar(0)

        # Grab a set of interpolated data
        key_unit = units.Unit.get_unit(self.mfg_data.units[0])
        scalar_value = self.diameter(key_unit)
        self.interpolated_data = interpolate_lookup(self.mfg_data.data, scalar_value)

    def interpolate(self, what):
        """ Using the manufactuing table and the diameter, interpolate a data """
        index = self.mfg_data.fields[1].index(what)
        unit = units.Unit.get_unit(self.mfg_data.units[1][index])
        return unit(round_significant(self.interpolated_data[index]))
    
    @classmethod
    def get_from_stock(cls, diameter, allow_bigger=False):
        """ Get the nearest matching bit size from our stock """
        standard_sizes = sorted([k(units.um) for k in cls.__stock__])
        v = min_so_far = diameter(units.um)
        retval = None

        # Start with the largest bit - rational : A bigger hole will accomodate the part
        # In most cases, the plating (0.035 nominal) will make the hole smaller in the end
        for s in reversed(standard_sizes):
            lower = v - v * config.gs.downsizing_allowance_percent / 100
            upper = v + v * config.gs.oversizing_allowance_percent / 100

            # Skip too large of a hole
            if allow_bigger:
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
                    return s

                retval = s

        return diameter.unit(retval * units.um)


class DrillBit(CuttingTool):
    __stock__ = config.stock.drillbits

    def __init__(self, diameter):
        super().__init__(diameter, config.md.drillbits)
        self.cut_direction = CutDir.UP

        self.rpm = self.interpolate("speed")
        self.z_feedrate = self.interpolate("z_feed")

    def __repr__(self) -> str:
        return f"{self.diameter} {self.rpm} zfeed:{self.z_feedrate}"


class RouterBit(CuttingTool):
    __stock__ = config.stock.routerbits

    def __init__(self, diameter):
        super().__init__(diameter, config.md.routerbits)
        self.cut_direction = CutDir.UPDOWN

        self.rpm = self.interpolate("speed")
        self.z_feedrate = self.interpolate("z_feed")
        self.table_feed = self.interpolate("table_feed")
        self.exit_depth = self.interpolate("exit_depth")

    def __repr__(self) -> str:
        return f"{self.diameter} {self.rpm} zfeed:{self.z_feedrate} feed:{self.table_feed}"


if __name__ == "__main__":
    db = DrillBit(2.07 * units.mm)
    print(db)

    rb = RouterBit(1.07 * units.mm)
    print(rb)

    v = DrillBit.get_from_stock(0.71 * units.mm)
    print(v)
    