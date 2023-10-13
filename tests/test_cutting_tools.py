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

from kicad2gcode.cutting_tools import DrillBit, RouterBit, CutDir, CuttingTool
from kicad2gcode.units import mm, rpm, mm_min, degree, inch, um
# pylint: disable=E0611 # The module is fully dynamic
from kicad2gcode.config import stock, global_settings as gs


def test_basic(monkeypatch):
    """ Test internals of a drill and router bits """
    # Set machining data so we can validate independantly
    # These are rounded to 4 digits
    DrillBit.__mfg_data__.data[2.0] = [11110, 12000]

    # Avoid the limit
    monkeypatch.setitem(gs["feedrates"]["z"], "max", 100000)

    db = DrillBit(2.0 * mm)

    assert db.type is DrillBit
    assert db.cut_direction is CutDir.UP
    assert db.diameter == mm(2)
    assert db.tip_angle == 135*degree
    assert db.rpm == rpm(11110)
    assert db.z_feedrate == mm_min(12000)

    # Set a limit
    monkeypatch.setitem(gs["feedrates"]["z"], "max", 10000)

    db = DrillBit(2.0 * mm)

    assert db.type is DrillBit
    assert db.cut_direction is CutDir.UP
    assert db.diameter == mm(2)
    assert db.tip_angle == 135*degree
    assert db.rpm == rpm(11110)
    assert db.z_feedrate == mm_min(10000)

    # Set machining data so we can validate independantly
    RouterBit.__mfg_data__.data[1.05] = [22220, 0.5, 0.6, 0.7]

    rb = RouterBit(1.05 * mm)

    assert rb.type is RouterBit
    assert rb.cut_direction is CutDir.UPDOWN
    assert rb.diameter == mm(1.05)
    assert rb.tip_angle == 180*degree
    assert rb.rpm == rpm(22220)
    assert rb.z_feedrate == mm_min(600)
    assert rb.table_feed  == mm_min(500)


def test_stock(monkeypatch):
    """ Test accessing bits from the stock """

    # Override the stock for this test
    monkeypatch.setitem(gs, "oversizing_allowance_percent", 10)
    monkeypatch.setitem(gs, "downsizing_allowance_percent", 10)
    monkeypatch.setitem(stock, "drillbits", [0.6*mm, 0.7*mm, 0.8*mm])
    monkeypatch.setitem(stock, "routerbits", [1.4*mm, 1.5*mm, 1.6*mm])

    v = DrillBit.get_from_stock(0.71 * mm)
    assert v.diameter == 0.7*mm

    v = RouterBit.get_from_stock(1.58 * mm)
    assert v.diameter == 1.5*mm


def test_request(monkeypatch):
    """ Test requesting cutting tools from the stock """
    # Override the stock for this test
    monkeypatch.setitem(gs, "oversizing_allowance_percent", 10)
    monkeypatch.setitem(gs, "downsizing_allowance_percent", 10)
    monkeypatch.setitem(stock, "drillbits", [0.6*mm, 0.7*mm, 2.0*mm])
    monkeypatch.setitem(stock, "routerbits", [0.9*mm, 1.5*mm, 1.6*mm])
    monkeypatch.setitem(gs, "router_diameter_for_contour", 2.0*mm)
    
    v_ok = CuttingTool.request(DrillBit(2*mm))
    assert v_ok and v_ok.type is DrillBit and v_ok.diameter == 2*mm

    v_fail = CuttingTool.request(RouterBit(0.84*mm))
    assert v_fail is None

    v_ok = CuttingTool.request(RouterBit(0.94*mm))
    assert v_ok and v_ok.type is RouterBit and v_ok.diameter == 0.9*mm

    # Too big
    v_fail = CuttingTool.request(RouterBit(1*inch))
    assert v_fail is None

    # Too small
    v_fail = CuttingTool.request(RouterBit(50*um))
    assert v_fail is None

    v_fail = CuttingTool.request(DrillBit(50*um))
    assert v_fail is None

    # Force routing
    v_router = CuttingTool.request(DrillBit(1/2*inch))
    assert v_router and v_router.type is RouterBit and v_router.diameter == 2.0*mm

    # Since the nearest bit is 0.7mm and the tolerance 10% - and since it cannot be routed - fail
    v_fail = CuttingTool.request(DrillBit(0.8*mm))
    assert v_fail is None
