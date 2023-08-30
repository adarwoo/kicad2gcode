from pcbgcode.config import config

import sys
print(sys.path)

def test_get_config():
   assert config.gs.spindle_speed.min