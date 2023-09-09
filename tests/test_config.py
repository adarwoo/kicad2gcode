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
""" Unit test for the global settints confituration """

# pylint: disable=E0611 # The module is fully dynamic
from pcb2gcode.config import global_settings as gs
from pcb2gcode.units import rpm


def test_global_settings():
    assert gs.spindle_speed.max.unit == rpm
    assert gs.spindle_speed.min.unit == rpm
