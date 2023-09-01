from pcb2gcode.cutting_tools import DrillBit, RouterBit, CutDir
from pcb2gcode.units import mm, rpm, mm_min, degree

def test_basic():
   db = DrillBit(2.0 * mm)

   assert db.type is DrillBit
   assert db.cut_direction is CutDir.UP
   assert db.diameter == mm(2)
   assert db.tip_angle == 135*degree
   assert db.rpm == rpm(20000)
   assert db.z_feedrate > 800 * mm_min

   rb = RouterBit(1.05 * mm)

def test_stock():
   v = DrillBit.get_from_stock(0.71 * mm)
   assert v.diameter == 0.7*mm

   v = RouterBit.get_from_stock(1.58 * mm)
   assert v.diameter == 1.5*mm
