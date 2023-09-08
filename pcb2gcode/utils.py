"""
Common utilities
"""
import bisect
from typing import List, Tuple, Set
import numpy as np
from python_tsp.exact import solve_tsp_dynamic_programming

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

def optimize_travel(coordinates: List[Coordinate], segments: Set[Tuple(int, int)]=[]) -> List[int]:
    """
    Apply the Travelling Salesman Problem to the positions
    the CNC will visit.
    @param coordinates: A list of coordinates to visit
    @param segments: Segments in the list. Holds a pair of indexes in the coordinates which
                     represents the segment. A segment has a traveling cost of 0
    @returns The permutation list
    """
    def get_distance_matrix(coordinates):
        """ Create a matrix of all distance using numpy """
        num_coords = len(coordinates)
        distance_matrix = np.zeros((num_coords, num_coords))

        for i in range(num_coords):
            for j in range(i + 1, num_coords):
                if (i, j) in segments or (j, i) in segments:
                    distance = 0
                else:
                    distance = np.linalg.norm(np.array(coordinates[i]) - np.array(coordinates[j]))

                # Assign distance to both (i, j) and (j, i) positions in the matrix
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance

        return distance_matrix

    retval = []

    if coordinates:
        distance_matrix = get_distance_matrix(coordinates)
        permutation, _ = solve_tsp_dynamic_programming(distance_matrix)

    return permutation

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
