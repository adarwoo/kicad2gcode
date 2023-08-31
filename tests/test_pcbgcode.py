from pcb2gcode.config import config


def test_get_config():
   assert config.gs.spindle_speed.min