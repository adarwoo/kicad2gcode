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
Common utilities
"""
import bisect
import numpy as np

from .coordinate import Coordinate


def round_significant(number, significant_digits=4):
    """ @return A rounded number """
    rounded = float("{:.{}g}".format(number, significant_digits))
    return int(rounded) if rounded.is_integer() else rounded

def interpolate_lookup(table, value):
    """
    Given a value, lookup the nearest values from the given table and
    extrapolate a value based on a linear extrapolation
    This function creates a virtual entry in the lookup table and return the virtual row.
    If the value exists in the table, the table entry is returned.
    """
    diameters = sorted(table.keys())
    index = bisect.bisect_left(diameters, value)

    # Handle edge cases
    if index == 0:
        return table[diameters[0]]
    if index == len(diameters):
        return table[diameters[-1]]

    # Interpolate values
    lower_diameter = diameters[index - 1]
    upper_diameter = diameters[index]
    lower_values = table[lower_diameter]
    upper_values = table[upper_diameter]

    lower_percentage = (upper_diameter - value) / (upper_diameter - lower_diameter)
    upper_percentage = 1 - lower_percentage

    interpolated_values = tuple(l * lower_percentage + u * upper_percentage
                                for l, u in zip(lower_values, upper_values))

    return interpolated_values


def interpolate_points(start: Coordinate, end: Coordinate, spacing):
    # Convert the start and end points to NumPy arrays
    start_point = np.array(start)
    end_point = np.array(end)

    # Calculate the distance and direction between start and end points
    direction = end_point - start_point
    distance = np.linalg.norm(direction)

    # Calculate the number of intermediate points required
    num_points = int(distance / spacing)

    # Generate the list of intermediate points
    intermediate_points = [
        start_point + i * (direction / num_points) for i in range(1, num_points)]

    return intermediate_points
