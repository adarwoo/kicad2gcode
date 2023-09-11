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

from pcb2gcode.rack import RackManager
from pcb2gcode.pcb_inventory import Inventory
from pcb2gcode.utils import Coordinate
from pcb2gcode.units import mm
from pcb2gcode.machining import Machining, Operations
from pcb2gcode.cutting_tools import DrillBit


inventory = Inventory()

holes = {
    0.8: [(1,  1), (1, 100), (100,  1), (100, 100)],
    0.5: [(21, 21), (21, 120), (120, 21), (120, 120)],
    1.2: [(41, 41), (41, 140), (140, 41), (140, 140)]
}

# Create a simple inventory
for dia, locs in holes.items():
    for x, y in locs:
        inventory.add_hole(Coordinate(x*mm, y*mm), dia*mm)


def test_simple():
    rack_man = RackManager()
    from_rack = rack_man.get_rack()
    machining = Machining(inventory)

    rack = machining.process(Operations.PTH)
    ops = from_rack.merge(rack)

    assert ops[0].name == "ADD" and ops[0].slot == 1 and ops[0].final_tool == DrillBit(
        0.5*mm)
    assert ops[1].name == "ADD" and ops[1].slot == 2 and ops[1].final_tool == DrillBit(
        0.8*mm)
    assert ops[2].name == "ADD" and ops[2].slot == 3 and ops[2].final_tool == DrillBit(
        1.2*mm)

    machining.use_rack(from_rack)
    machining.optimize()

    # Check operation re-ordered
    tool_number, ops = next(iter(machining.tools_to_ops.items()))

    assert tool_number == 1

    assert ops[0].tool.diameter == 0.5*mm
