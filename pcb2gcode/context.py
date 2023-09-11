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

# pylint: disable=W0106 # Clean construct for logging
"""
Create a single context object to allow access to the entire system information
to the GCode adapters in profile
"""

# Cutting tools for the CNC
from pathlib import Path

# pylint: disable=E0611 # The module is fully dynamic
from .config import global_settings as gs
# pylint: disable=E0611 # The module is fully dynamic
from .config import machining_data as md
# pylint: disable=E0611 # The module is fully dynamic
from .config import stock


class Context:
    """ Context object to pass compound information to adapters """
    def __init__(self) -> None:
        self.gs = gs
        self.md = md
        self.stock = stock

        # Name of the PCB file
        self.pcb_filename: Path = None

        # On-going operations
        self.operations: None

        # Machining instance
        self.machining = None

    @property
    def rack(self):
        """ Quick access to the rack """
        return self.machining.rack if self.machining else None


# Unique instance
ctx = Context()
