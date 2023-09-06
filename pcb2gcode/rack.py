#!/usr/bin/python3

# Rack management for the project
# If the CNC has automated changes, you want to create a standard
# rack, so most jobs will reuse the same tool position
# Can also be used to compute the wear of the bits in the rack

# Complex number are used where real part is a drill bit and the imaginary a router

from typing import Self

from collections import OrderedDict
from .config import global_settings as gs
from .cutting_tools import CuttingTool

from .cutting_tools import DrillBit

import logging
import os


logger = logging.getLogger(__name__)


class RackSetupOp:
    def __init__(self, slot, final_tool) -> None:
        self.slot = slot
        self.final_tool = final_tool


class RackAddTool(RackSetupOp):
    def __init__(self, slot, final_tool) -> None:
        super().__init__(slot, final_tool)


class RackReplaceTool(RackSetupOp):
    def __init__(self, slot, from_tool, final_tool) -> None:
        super().__init__(slot, final_tool)


class Rack:
    """
    Defines a rack object which behaves like a list of cutting tools and
    a dict to locate bits.
    A rack always has a size. If the size is 0, the rack is manual adn can grow
    without limits
    """
    def __init__(self, size=0):
        """
        Construct a rack.
        @param size The initial size of the rack. If size is 0, the rack is not
                    size bound.
        """
        self.rack = [None] * size # Else contains CuttingTools
        self.size = size
        self.invalid_slot = {}

    def __getitem__(self, key):
        return self.rack[key - 1]

    def __setitem__(self, key, value):
        self.rack[key - 1] = value

    def __delitem__(self, key):
        del self.rack[key - 1]

    def __contains__(self, key):
        return key in self.rack

    def __len__(self):
        return len(self.rack)

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
        self.invalid_slot.set(slot)

    def add_bit(self, bit, position=None, no_warn=False):
        """
        Add the bit to the rack.
        The bit must be a cutting tool or None
        If the position is None, find the next available position which
         starts with the first available slot from the right
        Raise: ValueError if the rack is full
        """
        if self.size:
            if position is None:
                position = self.find_free_position()
            elif position < 1 or position > len(self.rack):
                if slot in self.invalid_slot:
                    logger.warning(f"Slot {slot} is not usable")
                raise ValueError("Invalid position")

            if self.rack[position - 1] is not None and not no_warn:
                logger.warning(
                    f"Warning: Slot {position} already occupied with "
                    "{self.rack[position - 1]}"
                )

        # Chech if the same diameter is not already occupied
        for dia, slot in self.items():
            if dia and bit == dia:
                logger.warning(
                    f"Warning: Bit {dia} in T{slot:02} "
                    "is already present in the rack at T{slot:02}. "
                    "This slot will not be used."
                )

        if self.size:
            self.rack[position - 1] = bit
        else:
            self.rack.append(bit)

    def merge(self, rack: Self):
        """
        Merge all the tools from the given rack into this one
        """
        operations = []

        for tool_to_set in rack.values():
            if tool_to_set not in self.keys():
                pos = self.find_free_position(False)

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
                        logger.error(f"Rack is full. Cannot add tool {tool_to_set}")
                else:
                    operations.append(RackAddTool(pos, tool_to_set))
                    self.add_bit(tool_to_set, pos)

    def diff(self, rack:Self):
        """
        Diff racks and compile a list of actions from the operator
        This rack is the final rack
        """
        retval = OrderedDict() # type: Dict[int, tuple[str, complex]]

        for slot in self.values():
            this_dia = self.rack[slot]
            their_dia = rack.get_tool(slot)

            if this_dia is None:
                continue

            if their_dia is None:
                retval[slot] = ("ADD", this_dia)
            else:
                retval[slot] = ("REPLACE", this_dia)

        return retval

    def remove_bit(self, bit):
        self.rack.remove(bit)

    def find_free_position(self, extend=True):
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

        for i in range(len(self.rack), 0, -1):
            zi = i - 1
            if self.rack[zi] is None:
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
        from .config import rack

        # Process the rack_data
        self.issue = rack.issue
        self.size = rack.size
        self.rack = Rack(self.size)

        self.selection = rack.use

    def save(self, RACK_FILE):
        # TODO
        pass

    def get_rack(self):
        """ @return A deep copy of the current rack """
        return self.rack.clone(False)

