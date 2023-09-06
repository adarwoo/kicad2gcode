from pcb2gcode.cutting_tools import DrillBit, RouterBit, CutDir, CuttingTool
from pcb2gcode.units import mm, rpm, mm_min, degree, inch, um
from pcb2gcode.config import stock

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

def test_request():
   v_ok = CuttingTool.request(DrillBit(2*mm))
   assert v_ok and v_ok.type is DrillBit and v_ok.diameter == 2*mm

   v_ok = CuttingTool.request(RouterBit(0.8*mm))
   assert v_ok and v_ok.type is RouterBit and v_ok.diameter == 0.8*mm

   # Too big
   v_fail = CuttingTool.request(RouterBit(1*inch))
   assert v_fail is None

   # Too small
   v_fail = CuttingTool.request(RouterBit(50*um))
   assert v_fail is None

   v_fail = CuttingTool.request(DrillBit(50*um))
   assert v_fail is None

   # Force routing
   v_fail = CuttingTool.request(DrillBit(1/2*inch))
   assert v_fail and v_fail.type is RouterBit and v_fail.diameter == 1.6*mm

   # Remove all router from stock
   stock["routerbits"] = [1*mm]
   stock["drillbits"] = [0.5*mm]

   # Since the only bit is 0.5mm and the tolerance 10% - and since it cannot be routed - fail
   v_fail = CuttingTool.request(DrillBit(0.75*mm))
   assert v_fail is None
