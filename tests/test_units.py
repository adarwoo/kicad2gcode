# Unit test for the units.py module

def test_simple():
   from pcb2gcode.units import mm

   v_mm = mm(10)
   assert str(v_mm) == "10mm"
   assert v_mm.value == 10
   assert v_mm.base == 10000

   v_mm = mm(15.45)
   assert str(v_mm) == "15.45mm"
   assert v_mm.value == 15.45
   assert v_mm.base == 15450

   v_mm = 7*mm
   assert str(v_mm) == "7mm"
   assert v_mm.value == 7
   assert v_mm.base == 7000

def test_lengths():
   from pcb2gcode.units import mm, cm, um, inch, mil, thou
   from pcb2gcode.units import Length

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
   from pcb2gcode.units import FeedRate
   from pcb2gcode.units import mm_min, cm_min, in_min, inch_min

   v_mm_min = 8 * mm_min
   assert v_mm_min.unit is mm_min
   assert v_mm_min.unit.type is FeedRate


def test_angle():
   from pcb2gcode.units import deg, degree, Angle

   v_deg = deg(360.0)
   v_degree = degree(180.0)
   assert v_deg() / 2 == v_degree()
   assert v_deg.unit is deg
   assert v_degree.unit is degree
   assert v_deg.unit.type is Angle


def test_conversion():
   from pcb2gcode.units import um, mm, cm

   v_mm = 80 * mm
   v_cm = cm(v_mm)
   assert v_cm.unit is cm
   assert v_cm.value == 8

   # Test float rounding errors
   r = um(700.0)
   r = mm(r)
   assert str(r) == "0.7mm"


def test_arithmetic():
   from pcb2gcode.units import mm, cm

   v_mm = 10 * mm
   v_cm = 5 * cm
   v_res = v_mm + v_cm
   assert v_res.value == 60


def test_array():
   from pcb2gcode.units import inch, mm

   array_inch = [3, 4, 6] * inch

   assert len(array_inch) == 3
   assert array_inch[0] == inch(3)
   assert array_inch[1] == inch(4)
   assert array_inch[2] == inch(6)

   assert inch(4) in set(array_inch)
   # TODO assert mm(6 * 25.4) in set(array_inch)


def test_from_string():
   from pcb2gcode.units import Length, FeedRate, Angle
   from pcb2gcode.units import mm, cm, inch
   from pcb2gcode.units import mm_min, cm_min, in_min, inch_min

   l = Length.from_string("4cm")
   assert l == cm(4)

   l = Length.from_string("4/3mm")
   # TODO assert l == mm(4/3)

   l = Length.from_string("8/9 in")
   # TODO assert l == inch(8/9)

   f = FeedRate.from_string("69/8   cm/min")
   # TODO assert l == cm_min(69/8)


def test_factory():
   from pcb2gcode.units import Unit, mm

   k = Unit.get_type("length").from_string("34.5mm")

   assert k==mm(34.5)
