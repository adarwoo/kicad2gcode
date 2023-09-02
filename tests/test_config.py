
def test_global_settings():
   from pcb2gcode.config import global_settings as gs
   from pcb2gcode.units import rpm

   assert gs.spindle_speed.max.unit == rpm
   assert gs.spindle_speed.min.unit == rpm

