from typing import List, Tuple, Dict

import bisect

from settings import *


M2U = lambda n: int(1e6*n)
U2M = lambda n: float(n/1e6)
TO_UM = lambda n: M2U(n) if type(n) is float or CHECK_WITHIN_DIAMETERS_ABSOLUTE_RANGE(n) else n
TO_MM = lambda n: U2M(n) if type(n) is int and not CHECK_WITHIN_DIAMETERS_ABSOLUTE_RANGE(n) else n
REAL = lambda n: n.imag if n.imag else n
DIA_TO_STR = lambda n: f"R{TO_MM(n.imag)}" if n.imag else f"{TO_MM(n)}"


# Lookup and interpolate a value from a
INTERPOLATE_LUT_AT = lambda value, table, pos, scale=1: (
    interpolate_lookup(table, value)[pos]*scale)


class Coordinate:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y


def find_nearest_drillbit_size(n, sizes=None, allow_bigger=True):
    """
    Find from the standard size, the nearest bit.
    Grab the neareast smaller and nearest larger and check within acceptable
    margin. The smallest difference wins.
    The units of n and sizes must be the same.

    @param n The diameter to drill. If the value is complex, it is a router
    @param sizes An array of sizes to choose from
    @param allow_bigger If True (default), allow a bit to be bigger than the hole
           If the bit is used to drill a pre-hole prior to routing, the bit should
           not be bigger and this should then be false

    @return The best matching bit size or None
    """
    # Use the default size
    if not sizes:
        sizes = ROUTERBIT_SIZES if n.imag else DRILLBIT_SIZES

    # Do not mix drill and router bits
    filtered_sizes = [hole for hole in sizes if hole.imag == n.imag]

    # Find the nearest number using the min function with a custom key function
    standard_sizes = sorted([s for s in sizes if isinstance(s, int)])
    min_so_far = n
    retval = None
    lower = lambda n: n - n*MAX_DOWNSIZING_PERCENT/100
    upper = lambda n: n + n*MAX_OVERSIZING_PERCENT/100

    # Start with the largest bit - rational : A bigger hole will accomodate the part
    # In most cases, the plating (0.035 nominal) will make the hole smaller in the end
    for s in reversed(filtered_sizes):
        # Skip too large of a hole
        if allow_bigger:
            if s > upper(n):
                continue
        elif s > n:
            continue

        # Stop if too small - won't get better!
        if s < lower(n):
            break

        # Whole size is ok, promote if difference is less
        if abs(n-s) < min_so_far:
            min_so_far = abs(n-s)

            if min_so_far == 0:
                return s

            retval = s

    return retval


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

    interpolated_values = tuple(int(l * lower_percentage + u * upper_percentage)
                                for l, u in zip(lower_values, upper_values))

    return interpolated_values

def optimize_travel(coordinates: List[Tuple[int,int]]) -> List[int]:
    """
    Apply the Travelling Salesman Problem to the positions
    the CNC will visit.
    @param coordinates A list of (x,y) coordinates to visit
    @returns A list containing the ordered position of each coordinate to visit
    """
    from python_tsp.exact import solve_tsp_dynamic_programming

    def get_distance_matrix(coordinates):
        """ Create a matrix of all distance using numpy """
        import numpy as np

        num_coords = len(coordinates)
        distance_matrix = np.zeros((num_coords, num_coords))

        for i in range(num_coords):
            for j in range(i + 1, num_coords):
                distance = np.linalg.norm(np.array(coordinates[i]) - np.array(coordinates[j]))

                # Assign distance to both (i, j) and (j, i) positions in the matrix
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance

        return distance_matrix

    retval = []

    if coordinates:
        distance_matrix = get_distance_matrix(coordinates)
        permutation, distance = solve_tsp_dynamic_programming(distance_matrix)
        retval = [coordinates[i] for i in permutation]

    return retval

def interpolate_points(start: Coordinate, end: Coordinate, spacing):
    import numpy as np

    # Convert the start and end points to NumPy arrays
    start_point = np.array(start)
    end_point = np.array(end)

    # Calculate the distance and direction between start and end points
    direction = end_point - start_point
    distance = np.linalg.norm(direction)

    # Calculate the number of intermediate points required
    num_points = int(distance / spacing)

    # Generate the list of intermediate points
    intermediate_points = [start_point + i * (direction / num_points) for i in range(1, num_points)]

    return intermediate_points
