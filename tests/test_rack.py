from pcb2gcode.rack import Rack
from pcb2gcode.cutting_tools import DrillBit, RouterBit
from pcb2gcode.units import mm


def test_manual():
   r = Rack()

   r.add_bit(DrillBit(0.8*mm))
   r.add_bit(DrillBit(1.0*mm))
   r.add_bit(DrillBit(0.95*mm))
   r.add_bit(DrillBit(1.15*mm))
   r.add_bit(RouterBit(1*mm))

   t = r.get_tool(1)
   assert t.type is DrillBit and t.diameter == 0.8*mm
   t = r.get_tool(2)
   assert t.type is DrillBit and t.diameter == 1*mm
   t = r.get_tool(3)
   assert t.type is DrillBit and t.diameter == 0.95*mm
   t = r.get_tool(4)
   assert t.type is DrillBit and t.diameter == 1.15*mm
   t = r.get_tool(5)
   assert t.type is RouterBit and t.diameter == 1*mm

   t = r.get_tool(0)
   assert t is None
   t = r.get_tool(6)
   assert t is None

   # Test dict behaviour
   assert DrillBit(0.8*mm) in r
   assert RouterBit(4*mm) not in r
   assert RouterBit(1.0*mm) in r
   assert DrillBit(1.15*mm) in r

   assert len(r) == 5

def test_atc():
   r = Rack(4)

   # Set tool #2
   r.add_bit(DrillBit(0.8*mm), 2)

   # Add another. Should be in slot 3
   r.add_bit(DrillBit(1.8*mm))
   r.add_bit(DrillBit(1.9*mm))
   r.add_bit(RouterBit(0.8*mm))
   
   assert r.get_tool(3).diameter == 1.8*mm
   assert r.get_tool(4).diameter == 1.9*mm
   assert r.get_tool(1).diameter == 0.8*mm and r.get_tool(1).type is RouterBit

def test_sort():
   r = Rack()

   r.add_bit(DrillBit(1.8*mm))
   r.add_bit(RouterBit(0.8*mm))
   r.add_bit(DrillBit(1.9*mm))
   r.add_bit(DrillBit(2.6*mm))
   r.add_bit(RouterBit(1.8*mm))
   r.add_bit(DrillBit(0.9*mm))
   r.add_bit(RouterBit(1.2*mm))
   
   r.sort()
   
   assert r.get_tool(1).diameter == 0.9*mm and r.get_tool(1).type is DrillBit
   assert r.get_tool(2).diameter == 1.8*mm and r.get_tool(2).type is DrillBit
   assert r.get_tool(3).diameter == 1.9*mm and r.get_tool(3).type is DrillBit
   assert r.get_tool(4).diameter == 2.6*mm and r.get_tool(4).type is DrillBit
   assert r.get_tool(5).diameter == 0.8*mm and r.get_tool(5).type is RouterBit
   assert r.get_tool(6).diameter == 1.2*mm and r.get_tool(6).type is RouterBit
   assert r.get_tool(7).diameter == 1.8*mm and r.get_tool(7).type is RouterBit
  

def test_sort2():
   r = Rack(5)
   r.invalidate_slot(4)

   # Set tool #2
   r.add_bit(DrillBit(0.85*mm), 2)

   # Add another. Should be in slot 3
   r.add_bit(DrillBit(1.8*mm))
   # Skip 4 to go into 5
   r.add_bit(DrillBit(1.9*mm))
   # And 1
   r.add_bit(DrillBit(0.55*mm))
   
   r.sort()
   
   assert r.get_tool(1).diameter == 0.55*mm
   assert r.get_tool(2).diameter == 0.85*mm
   assert r.get_tool(3).diameter == 1.8*mm
   assert r.get_tool(4) == None
   assert r.get_tool(5).diameter == 1.9*mm
