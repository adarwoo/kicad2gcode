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

""" Unit test for the units.py module """
import pytest

from kicad2gcode.units import Unit, Length, FeedRate, Angle, Rpm
from kicad2gcode.units import cm_min, mm_min, in_min, inch_min, m_min, ipm
from kicad2gcode.units import deg, degree, rpm
from kicad2gcode.units import mm, cm, um, inch, mil, thou


def test_simple():
    v_mm = mm(10)
    assert str(v_mm) == "10mm"
    assert v_mm.value == 10
    assert v_mm.base == 10000000

    v_mm = mm(15.45)
    assert str(v_mm) == "15.45mm"
    assert v_mm.value == 15.45
    assert v_mm.base == 15450000

    v_mm = 7*mm
    assert str(v_mm) == "7mm"
    assert v_mm.value == 7
    assert v_mm.base == 7000000

    with pytest.raises(TypeError):
        v_mm == "7mm"


def test_lengths():
    v_mm = mm(25.4)
    v_cm = cm(2.54)
    v_um = um(25400)
    v_inch = inch(1)
    v_mil = mil(1000)
    v_thou = thou(1000)

    assert v_mm == v_cm
    assert v_cm == v_um
    assert v_inch == v_um
    assert v_um == v_inch
    assert v_inch == v_mil
    assert v_mil == v_thou

    assert v_mm.unit is mm
    assert v_cm.unit is cm
    assert v_um.unit is um
    assert v_inch.unit is inch
    assert v_mil.unit is mil
    assert v_thou.unit is thou

    assert v_mm.unit.type is Length
    assert v_cm.unit.type is Length
    assert v_um.unit.type is Length
    assert v_inch.unit.type is Length
    assert v_mil.unit.type is Length
    assert v_thou.unit.type is Length


def test_feedrates():
    """ Test all feedrates """
    v_mm_min = 8 * mm_min
    assert v_mm_min.unit is mm_min
    assert v_mm_min.unit.type is FeedRate
    v_m_min = 0.4 * m_min
    assert v_m_min == 400 * mm_min
    assert 1 * ipm == 1 * in_min
    assert 1 * ipm == 1 * inch_min
    assert 1 * ipm == 25.4 * mm_min


def test_angle():
    v_deg = deg(360.0)
    v_degree = degree(180.0)
    assert v_deg() / 2 == v_degree()
    assert v_deg.unit is deg
    assert v_degree.unit is degree
    assert v_deg.unit.type is Angle


def test_conversion():
    v_mm = 80 * mm
    v_cm = cm(v_mm)
    assert v_cm.unit is cm
    assert v_cm.value == 8

    # Test float rounding errors
    r = um(700.0)
    r = mm(r)
    assert str(r) == "0.7mm"


def test_arithmetic():
    v_mm = 10 * mm
    v_cm = 5 * cm
    v_res = v_mm + v_cm
    assert v_res.value == 60
    v_res = v_cm + 10
    assert v_res == 15


def test_array():
    array_inch = [3, 4, 6] * inch

    assert len(array_inch) == 3
    assert array_inch[0] == inch(3)
    assert array_inch[1] == inch(4)
    assert array_inch[2] == inch(6)

    assert inch(4) in set(array_inch)
    assert mm(6 * 25.4) in set(array_inch)


def test_from_string():
    l = Length.from_string("4cm")
    assert l == cm(4)
    assert l == mm(40)

    l = Length.from_string("4/3mm")
    assert l == mm(4/3)

    l = Length.from_string("8/9 in")
    assert l == inch(8/9)

    f = FeedRate.from_string("69/8   cm/min")
    assert f == cm_min(69/8)

    f = FeedRate.from_string("254ipm")
    assert f == in_min(254)
    assert f == inch_min(254)

    with pytest.raises(AssertionError):
        f == inch(254)

    a = Angle.from_string("360")
    assert a() == 360
    assert a == deg(360)
    assert a == degree(360)

    with pytest.raises(AssertionError):
        a == rpm(360)

    r = Rpm.from_string("12500")
    assert r() == 12500

    r = Rpm.from_scalar(12500)
    assert r == 12500 * rpm


def test_factory():
    k = Unit.get_type("length").from_string("34.5mm")

    retval = (k == mm(34.5))
    assert retval


def test_multiply():
    a = [3, 4, 6]
    b = a * mm
    assert b[0] == mm(3)
    assert b[1] == mm(4)
    assert b[2] == mm(6)

    a = mm(7)
    assert a * 10 == mm(70)

    b = a * [1, 2, 4]
    assert b[0] == mm(7)
    assert b[1] == mm(14)
    assert b[2] == mm(28)

    # We don't support mm*mm!
    with pytest.raises(TypeError):
        b = a * mm(6)


def test_misc():
    my_mm = Unit.get_unit("mm")
    assert my_mm is mm

def test_operators():
    l1 = Length.from_string("4cm")
    l2 = Length.from_string("40mm")
    l3 = Length.from_string("4.1cm")
    l4 = Length.from_string("41mm")

    assert l1 == cm(4)
    assert l1 == mm(40)

    assert l2 == l2
    assert l1 == l1
    assert l1 == l2
    assert l2 == l1

    assert l2 <= l2
    assert l1 <= l1
    assert l1 <= l2
    assert l2 <= l1
    assert l1 <= l3
    assert l1 <= l4

    assert not (l4 <= l1)
    assert not (l3 <= l1)

    assert l2 >= l2
    assert l1 >= l1
    assert l2 >= l1
    assert l1 >= l2
    assert l3 >= l1
    assert l4 >= l1

def test_rounding():
    """ Test the units rounding function """
    l1 = 32.456456*mm
    res = 5*um

    res = l1.round(res)

    assert res == 32.455 * mm