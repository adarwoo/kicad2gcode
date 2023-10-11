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

import sys
import os
from pathlib import Path

import pytest

from pcb2gcode.machining import Machining
from pcb2gcode.operations import Operations


@pytest.mark.skipif('CODESPACES' in os.environ or 'CI' in os.environ, reason="No KiCAD setup in CI")
def test_simple_file():
    """ Test real life situation with a test PCB """
    from pcb2gcode.board_processor import BoardProcessor

    # Load from this folder
    this_path = Path(__file__).resolve().parent
    pcb_file_path = this_path / "pulsegen.kicad_pcb"

    processor = BoardProcessor(pcb_file_path)

    # Create a machining object for our operations
    machining = Machining(processor.inventory)

    # Process the inventory for the given operations
    required_rack = machining.process(Operations.ALL)

    print(required_rack)

    # Optimize all displacements
    machining.optimize()

    # Generate the GCode
    machining.generate_machine_code(sys.stdout)
