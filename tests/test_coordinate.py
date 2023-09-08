import numpy
from pcb2gcode.units import mm
from pcb2gcode.coordinate import Coordinate

def test_basic():
    a = Coordinate(2*mm, 4*mm)
    
    assert a.x == mm(2)
    assert a.y == mm(4)
    
    n = numpy.array(a)
    
    assert n[0] == mm(2).base
    assert n[1] == mm(4).base
