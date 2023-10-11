# -*- coding: utf-8 -*-

#
# This file is part of the kicad2gcode distribution (https://github.com/adarwoo/kicad2gcode).
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

import numpy
from kicad2gcode.units import mm
from kicad2gcode.coordinate import Coordinate


def test_basic():
    a = Coordinate(2*mm, 4*mm)

    assert a.x == mm(2)
    assert a.y == mm(4)

    n = numpy.array(a)

    assert n[0] == mm(2).base
    assert n[1] == mm(4).base
