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
List machining operations for a PCB.

    - PTH stands for Platted Through Hole.
        * To create platted through PCBs, a bare board is drilled first.
        The holes are then electro-chemically platted:
        - activation
        - electroless platting
        - eletro-platting
    - NPTH is for non-platted holes
        * Once a board has been platted, it is etched
        - Solder resist mask
        - Tenting or tining
        - Etch
        - Stripping
        * Then, the non-platted holes must be drilled
    - OUTLINE for routing the outline
        * This is the last operation since the board reaches it's final size
        * Tabs can be added, so the larger board can be used for:
        - applying solder paste
        - testing the board
    
    - ALL is typically for single sided board which are etched and don't need PTH
        * Most holes are still identified as PTH but are drilled along with NPTH
        * Final routing is applied too
    
    - FIRST is the same of PTH

    - FINAL is to do the final drills and route the contour.
"""

from enum import IntEnum


class Operations(IntEnum):
    """ Used to tell the Machining class which holes to do """
    NONE = 0
    PTH = 0b0001        # Includes routing oblongs
    NPTH = 0b0010       # Includes routing oblongs
    OUTLINE = 0b0100    # Only routing of the outline
    
    FIRST = PTH
    FINAL = NPTH | OUTLINE
    ALL = FIRST | FINAL
