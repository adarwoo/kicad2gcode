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
Rack management for the project
If the CNC has automated changes, you want to create a standard
rack, so most jobs will reuse the same tool position
Can also be used to compute the wear of the bits in the rack
"""
import logging
from collections import OrderedDict
from typing import List

from .cutting_tools import CuttingTool, DrillBit, RouterBit


logger = logging.getLogger(__name__)


class RackSetupOp:
    """ Abstract base class for all rack setup operations """
    def __init__(self, slot, name, final_tool) -> None:
        self.slot = slot
        self.final_tool = final_tool
        self.name = name

    def __repr__(self) -> str:
        return f"T{self.slot:02}: {self.name} {self.final_tool}"


class RackAddTool(RackSetupOp):
    """ Operation where a tool shall be added to a vacant slot """
    def __init__(self, slot, final_tool) -> None:
        super().__init__(slot, "ADD", final_tool)


class RackReplaceTool(RackSetupOp):
    """ Operation where a tool shall be replaced by another """
    def __init__(self, slot, from_tool, final_tool) -> None:
        super().__init__(slot, "REPLACE", final_tool)
        self.from_tool = from_tool

    def __repr__(self) -> str:
        return f"T{self.slot:02}: REPLACE {self.from_tool} WITH {self.final_tool}"


class Rack:
    """
    Defines a rack object which behaves like a list of cutting tools and
    a dict to locate bits.
    A rack always has a size. If the size is 0, the rack is manual and can grow
    without limits.
    To access a tool, always use the get_tool accessor which is indexed from 1.
    Standard List function are zero indexed.
    """
    def __init__(self, size=0):
        """
        Construct a rack.
        @param size The initial size of the rack. If size is 0, the rack is not
                    size bound.
        """
        self.rack = [None] * size # Else contains CuttingTools
        self.size = size
        self.invalid_slot = set()

    def __getitem__(self, key):
        return self.rack[key]

    def __setitem__(self, key, value):
        self.rack[key] = value

    def __delitem__(self, key):
        del self.rack[key]

    def __contains__(self, key):
        return key in self.rack

    def __len__(self):
        return len(self.rack)

    @property
    def is_manual(self):
        return self.size == 0

    def clone(self, unbound=True):
        """ @returns A deep copy of the rack, unbound in size """
        from copy import deepcopy

        retval = type(self)(self.size if not unbound else 0)
        retval.rack = deepcopy(self.rack)

        return retval

    def items(self):
        return [(bit, i) for i, bit in enumerate(self.rack, start=1)]

    def keys(self):
        return self.rack

    def values(self):
        return list(range(1, len(self.rack) + 1))

    def get_tool(self, slot):
        """ @return The tool in the given T slot or None """
        if slot < 1 or slot > len(self.rack):
            return None

        return self.rack[slot-1]

    def invalidate_slot(self, slot):
        """
        Renders the given slot (indexed from 1) not in use
        """
        self.invalid_slot.add(slot)

    def add_bit(self, bit: CuttingTool, position=None, no_warn=False):
        """
        Add the bit to the rack.
        The bit must be a cutting tool or None
        If the position is None, find the next available position which
         starts with the first available slot from the right
        Raise: ValueError if the rack is full
        """
        retval = None

        if self.size:
            if position is None:
                position = self.find_free_position()
            elif position < 1 or position > len(self.rack):
                if position in self.invalid_slot:
                    logger.warning("Slot %d is not usable", position)

                raise ValueError("Invalid position")

            if self.rack[position - 1] is not None and not no_warn:
                logger.warning(
                    "Warning: Slot %d already occupied with %s", position, self.rack[position - 1]
                )

        # Chech if the same diameter is not already occupied
        for dia, slot in self.items():
            if dia and bit == dia:
                logger.warning(
                    "Warning: Bit %s in T%.2d is already present in the rack at T%.2d.\n"
                    "This slot will not be used.", dia, position, slot
                )

        if self.size:
            retval = position - 1
            self.rack[retval] = bit
        else:
            self.rack.append(bit)
            retval = len(self.rack)

        return retval

    def merge(self, rack) -> List[RackSetupOp]:
        """
        Merge all the tools from the given rack into this one
        """
        operations = []

        for tool_to_set in rack.keys():
            if tool_to_set not in self.keys():
                pos = self.find_free_position()

                if pos is None:
                    # Look for unused bits in the rack and replace them
                    replaced = False

                    for tool_to_replace, slot in reversed(self.items()):
                        if tool_to_replace not in rack:
                            # Replace
                            self.add_bit(tool_to_set, slot, True)
                            operations.append(RackReplaceTool(slot, tool_to_replace, tool_to_set))
                            replaced = True
                            break

                    if not replaced:
                        logger.error("Rack is full. Cannot add tool {%s}", tool_to_set)
                else:
                    self.rack[pos-1] = tool_to_set
                    operations.append(RackAddTool(pos, tool_to_set))

        return operations

    def remove_bit(self, bit):
        self.rack.remove(bit)

    def find_free_position(self):
        """
        Return a tool position position in the rack which is free.
        By default, it will return the last position from the end which
        is free, otherwise, the next position from the end
        Rationale: If a space is left at the start - it usually serves a
        specific function.
        Note: Tool position starts from 1.

        x x x i x i x x
        """
        retval = None
        extend = (self.size == 0)

        for i in range(len(self.rack), 0, -1):
            zi = i - 1
            if (self.rack[zi] is None) and (zi not in self.invalid_slot):
                retval = i
                continue
            else:
                if retval:
                    break

        if retval is None:
            if extend:
                self.rack.append(None)
                retval = len(self.rack)

        return retval

    def request(self, what: CuttingTool, warn=True):
        """
        Request a cutting tool from the rack.
        The tool is first standardized, then searched in the rack.
        If the tool cannot be found, it is added to the rack

        Args:
            what (CuttingTool): A cutting tool
        @returns The ID of the slot
        """
        # Grab a standard cutting tool
        retval = CuttingTool.request(what, warn)

        if not retval:
            raise ValueError("Cannot get bit size from stock")

        # Locate in this rack
        for tool, slot in self.items():
            if tool == retval:
                return slot

        # Not found add it
        return self.add_bit(retval)

    def sort(self):
        """
        Reorganise the rack by tool type and diameter
        """
        if self.is_manual:
            self.rack.sort()
        else:
            # Create an empty and unlimited rack
            newrack = []
            for bit in self.rack:
                if bit:
                    newrack.append(bit)

            # Sort it
            newrack.sort()

            # Reset the rack
            self.rack = [None] * self.size

            # Put sorted elements in
            index = 0
            for bit in newrack:
                while (index+1) in self.invalid_slot:
                    index += 1
                self.rack[index] = bit
                index+=1

    def __repr__(self):
        rack_str = ""
        for (id, t) in enumerate(self.rack):
            if t is None:
                rack_str += f"T{id+1:02}:x "
            else:
                tt = " " if t.type is DrillBit else "R"
                dia = t.diameter
                rack_str += f"T{id+1:02}:{tt}{dia} "

        return rack_str


class RackManager:
    """
    Object which manages the racks of the CNC.
    If the CNC has automated tool change, this is very important to
    allow the operator reusing existing racks.
    Depending on the CNC, the racks could be loadable, so each Job could
    have its own rack.
    The machining code can also create a new rack from scratch, and it
    can be saved.
    Finally for the less fortunate, the rack 'manual', is used to manually
    change the tools, and is considered of size unlimited.
    """
    def __init__(self) -> None:
        from .config import rack as rc

        # Process the rack_data
        self.issue = rc.issue
        self.size = rc.size
        self.racks = OrderedDict()

        for id, tools in rc.racks.items():
            rack = Rack(self.size)
            current_slot = 1

            for tool in tools:
                if "slot" in tool:
                    current_slot = tool["slot"]
                else:
                    current_slot += 1

                if tool.get("use", True) is False:
                    rack.invalidate_slot(current_slot)
                elif "drill" in tool:
                    rack.add_bit(DrillBit(tool["drill"]))
                elif "router" in tool:
                    rack.add_bit(RouterBit(tool["drill"]))
                else:
                    assert False, "unreachable"

            self.racks[id] = rack

        use = rc.get("use", None)

        if use:
            if use in self.racks:
                self.rack = self.racks[use]
            else:
                logger.error("'use'='%s' does not match any given rack. Ignoring.", use)
        else:
            self.rack = Rack(self.size)

    def save(self, RACK_FILE):
        # TODO
        pass

    def get_rack(self):
        """ @return A deep copy of the current rack """
        return self.rack.clone(False)

