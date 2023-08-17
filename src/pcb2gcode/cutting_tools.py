# Cutting tools for the CNC
from enum import IntEnu; 

class CuttingTool:
    class CutDir(IntEnum):
        UNKWOWN,
        UP,
        DOWN,
        UPDOWN

    class Geometry(IntEnum):
        ANGLED,
        FLAT
        
    def __new__(cls, *args, **kwargs):
        print("Creating instance of", cls.__name__)
        return super().__new__(cls)

    def __init__(self, diameter):
        self.type = __cls__.__name__
        self.diameter_um = 0
        self.tip_angle = 180
        self.cut_direction = CutDir
        self.rpm = 0
        self.z_feedrate = 0

class DrillBit(CuttingTool):
    pass

class RouterBit(CuttingTool):
    pass

