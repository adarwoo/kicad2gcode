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
Creates the machining GCode based on a Rack and Inventory

Provides the 'Machining' class which uses the Inventory to check
 all machining aspects, like creating the rack and generating the GCode.
Dimensions are kept as um until the GCode rendering
"""

from collections import OrderedDict
from typing import List, Dict, Set
from io import BufferedIOBase
import logging
import numpy as np

from python_tsp.exact import solve_tsp_dynamic_programming

# pylint: disable=E0611 # The module is fully dynamic
from .config import global_settings as gs

from .pcb_inventory import Inventory, Oblong, Hole, Route
from .units import mm
from .coordinate import Coordinate
from .rack import Rack
from .cutting_tools import DrillBit, RouterBit
from .operations import Operations


logger = logging.getLogger(__name__)


def optimize_travel(coordinates: List[Coordinate], segments: Set[int]=None) -> List[int]:
    """
    Apply the Travelling Salesman Problem to the positions the CNC will visit.
    @param coordinates: A list of coordinates to visit
    @param segments: Segments in the list. Holds a pair of indexes in the coordinates which
                     represents the segment. A segment has a traveling cost of 0
    @returns The permutation list
    """
    if segments is None:
        segments = set()
    
    def get_distance_matrix(coordinates):
        """ Create a matrix of all distance using numpy """
        num_coords = len(coordinates)
        distance_matrix = np.zeros((num_coords, num_coords))

        for i in range(num_coords):
            for j in range(i + 1, num_coords):
                if i in segments and j == i + 1:
                    distance = 0
                else:
                    distance = np.linalg.norm(np.array(coordinates[i]) - np.array(coordinates[j]))

                # Assign distance to both (i, j) and (j, i) positions in the matrix
                distance_matrix[i, j] = distance
                distance_matrix[j, i] = distance

        return distance_matrix

    if coordinates:
        distance_matrix = get_distance_matrix(coordinates)
        permutation, _ = solve_tsp_dynamic_programming(distance_matrix)

    return permutation


class Move:
    """ Abstract base class for machining actions """
    def __init__(self, start, end) -> None:
        """ Construct a basic move. Each move has a start and end """
        self.next = None
        self.start = start
        self.end = end
        
    def append(self, next):
        """ Append a move after this one """
        move = self
        while move.next:
            move = self.next
        move.next = next
        
    def last(self):
        """ Returns the last combined action """
        current = self
        while current.next:
            current = current.next
        return current


class LinearMove(Move):
    """ Machining a straight line (router) """
    pass

class ArcMove(Move):
    pass


class MachiningOperation:
    """
    A single machining operation which can result in many GCode being issued
    """
    def __init__(self, origin, tool) -> None:
        self.origin = origin
        self.tool = tool
        # Allow grouping operations which TSP should not optimize
        self.next_op = None
        
    def then(self, next):
        """
        Group operations in the same cycle
        These will not be optimized through the TSP algo.
        """
        to_next = self
        while to_next.next_op:
            to_next = self.next_op
        to_next.next_op = next
        
    def get_end_coordinate(self, first=True):
        """
        Consider the end coordinate of the machining operation
        @returns The end coordinate or None if it is the same as the start
        """
        if self.next_op:
            return self.next_op.get_end_coordinate(False)
        
        return None if first else self.origin
        
    def to_gcode_first(self, stream: BufferedIOBase, next=None):
        """ First operation for modal commands """
        raise RuntimeError
    
    def to_gcode_next(self, stream: BufferedIOBase, next=None):
        """ Following operation for modal commands """
        self.to_gcode_first(stream, next)
        
    def to_gcode_last(self, stream: BufferedIOBase):
        """ Chance to end a canned cycle """
        
    def __lt__(self, other):
        """ Override to sort by tool type """
        return self.tool < other.tool


class NoOperation(MachiningOperation):
    """ A dummy operation to allow creating segments during the optimization """
    def __init__(self) -> None:
        super().__init__(None, None)


class DrillHole(MachiningOperation):
    """
    Simplest of all operations - drill a hole
    This operation is modal
    """
    def to_gcode_first(self, stream: BufferedIOBase, next=None):
        stream.write(f"G4 X{self.origin.x(mm)} Y{self.origin.x(mm)}")


class RouteHole(MachiningOperation):
    """
    Use a router bit to route a hole.
    Starts from the center, moves to the top or goes round.
    """
    def __init__(self, origin, tool) -> None:
        super().__init__(origin, tool)

    def to_gcode_first(self, stream: BufferedIOBase, next=None):
        stream.write(f"G0 X{self.origin.x(mm)} Y{self.origin.x(mm)}")


class RouteVector(MachiningOperation):
    def __init__(self, move: Move, tool) -> None:
        super().__init__(move.orgin, tool)
        self.vector_start = move

    def get_end_coordinate(self, first=True):
        """ Override """
        retval = super().get_end_coordinate(first)
        
        if not retval:
            retval = self.vector_start.last().end
            
        return retval
    

class Machining:
    def __init__(self, inventory: Inventory):
        self.inventory = inventory

        # All operations in any order
        self.ops: List[MachiningOperation] = []

        # Drill ops for each tool in the rack
        self.tools_to_ops: Dict[int, List[MachiningOperation]] = OrderedDict()
        
    def process(self, ops: Operations):
        """
        Compile a list of all machining operations required.
        Use an umlimited rack to start with.
        You must call use_rack to finalised the operations
        
        Returns the default rack required. This rack can be used to merge
        with a specified rack. Internal operations are based on this rack.
        """
        # Start with an open rack (no tools and unlimited)
        rack = Rack()
        
        # Start with inspecting every holes to be made
        features = self.inventory.get_features(ops)
       
        for by_diameter in features.values():
            for feature in by_diameter:
                try:
                    # Oblong holes may require routing
                    if isinstance(feature, Oblong):
                        limit = feature.diameter * gs.slot_peck_drilling.max_length_to_bit_diameter
                        
                        if feature.distance > limit:
                            # Route using a single stroke
                            tool = RouterBit(feature.diameter)
                            tool_id = rack.request(tool)
                            self.ops.append(
                                RouteVector(LinearMove(feature.coord, feature.end), tool)
                            )

                        else:
                            tool = DrillBit(feature.diameter)
                            tool_id = rack.request(tool)
                            
                            # Start by drilling start and end
                            op = DrillHole(feature.coord, tool)
                            op.then(DrillHole(feature.end, tool))
                            self.ops.append(op)
                            
                            # Drill intermediate
                            x1, y1 = feature.coord()
                            x2, y2 = feature.end()
                            l = tool.diameter / gs.slot_peck_drilling.pecks_per_hole

                            distance = ((x2 - x1)**2 + (y2 - y1)**2)**0.5
                            total_points = int((distance / l).value)

                            for i in range(1, total_points + 1):
                                ratio = i / total_points
                                x = x1 + (x2 - x1) * ratio
                                y = y1 + (y2 - y1) * ratio
                                op.then(DrillHole(Coordinate(x, y), tool))
                                
                            self.ops.append(op)
                            
                    elif isinstance(feature, Hole):
                        tool = DrillBit(feature.diameter)
                        tool_id = rack.request(tool)
                        self.ops.append(DrillHole(feature.coord, tool))
                    
                    elif isinstance(feature, Route):
                        tool_id = rack.request(RouterBit(feature.diameter))
                    else:
                        raise RuntimeError
                except ValueError:
                    logger.error("No solution exist for a tool request")

        # Reorder the rack prior to returning it
        rack.sort()
        
        # Map the operation to our unlimited rack for now
        self.use_rack(rack)

        # Return the rack
        return rack
    
    def use_rack(self, rack: Rack):
        """
        Give a rack to use. The rack should have all tools required.
        This creates a non-optimized sorted list of operation based on tool type and diameter.
        The drills go first, smallest to largest bit. Then the routers.
        This operation is necessary to assign a tool number to the machining operation now
        the rack is known.
        """
        # Reset the ops
        self.tools_to_ops = OrderedDict()
        
        # Sort the operations by 'drill' first, smallest first, router
        for op in sorted(self.ops):
            # Grab tool
            tool_id = rack.request(op.tool)
            self.tools_to_ops.setdefault(tool_id, []).append(op)
            
    def optimize(self):
        """
        Optimize the travel from one machining to the next.
        The idea is to minimize the G0 travels.
        This is actually a well known - and suprisingly - complex subject known
        as the Traveling Salesman Problem.
        A brute force approach defeats any computer very quickly as the number of
        combination of this case is (n-1)!/2 - that's 5e155 combinations for 100 holes.
        So heuristic algorithms are used instead. The simplest one, consist in moving to
        the closest hole next, turns out to be > 90% efficient.
        Here, we rely on numpy and a TSP library to do the hard work - so we're
        likely better than 90% - whilst keeping the compute time under control.
        For the router parts, we use a trick where the routed path (start to end) have 0 cost
        in the graph, allowing for one algo fits all approach.
        """
        def get_distance_matrix(coordinates):
            """ Create a matrix of all distance using numpy """
            num_coords = len(coordinates)
            distance_matrix = np.zeros((num_coords, num_coords))

            for i in range(num_coords):
                for j in range(i + 1, num_coords):
                    if i in segments and j == i + 1:
                        distance = 0
                    else:
                        distance = np.linalg.norm(np.array(coordinates[i]) - np.array(coordinates[j]))

                    # Assign distance to both (i, j) and (j, i) positions in the matrix
                    distance_matrix[i, j] = distance
                    distance_matrix[j, i] = distance

            return distance_matrix
        
        # Apply TSP to each tool
        for tool_ops in self.tools_to_ops.values():
            # Create a matrix of travels with cost
            # Router are specials in than they have a zero cost to go from A to B
            coordinates = []
            # Indexes of segment start position. The end of the segment is the next item
            segments = set()
            # List to permutate
            final_ops = []
            
            for op in tool_ops:
                final_ops.append(op)
                coordinates.append(op.origin)
                end_coordinate = op.get_end_coordinate()
                
                if end_coordinate:
                    coordinates.append(end_coordinate)
                    segments.add(len(coordinates))
                    final_ops.append(NoOperation())
                    
            # Apply TSP
            distance_matrix = get_distance_matrix(coordinates)
            permutation, _ = solve_tsp_dynamic_programming(distance_matrix)
            
            # Reorder, and drop the segments
            tool_ops.clear()
            
            for i in permutation:
                if not isinstance(final_ops[i], NoOperation):
                    tool_ops.append(final_ops[i])

    def generate_machine_code(self, stream: BufferedIOBase):
        # The operations are already sorted by tool type and diameter
        # We need to apply a TSP to each tool operation
        # Note: The TSP optimization ignores the tool location during tool change
        for ops in self.tools_to_ops.values():
            first = True
            last_index = len(ops) - 1
            
            for index, op in enumerate(ops):
                # Is there a next?
                if index == last_index:
                    next = None
                else:
                    next = ops[index+1]
                    
                if first:
                    op.to_gcode_first(stream, next)
                else:
                    first = False
                    op.to_gcode_next(stream, next)
                    
                if next is None:
                    op.to_gcode_last(stream)
