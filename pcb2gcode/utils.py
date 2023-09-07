from typing import List, Tuple, Dict
import bisect


class Coordinate:
    """
    Helper object to store coordinates which could be visited
    to be later rendered using different offset and scale.
    """
    def __init__(self, x: int, y: int):
        """ Construct using int """
        self.x = x
        self.y = y

def round_significant(number, significant_digits=4):
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
    intermediate_points = [
        start_point + i * (direction / num_points) for i in range(1, num_points)]

    return intermediate_points
