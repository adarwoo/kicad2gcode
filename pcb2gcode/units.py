#!/usr/bin/python3
import re
from operator import __lt__, __le__, __eq__, __ne__, __ge__, __gt__
from .utils import round_significant

# TODO -> such a libary implicitly doing loss of precision is ***@!
# Pb: The rounding error could impact (to test) finding the bit
def fround(f):
    # Round to 14 digits to prevent float rounding errors during conversion
    return round_significant(f, 14)


RE_NUMBER = re.compile(
    r'^\s*(?P<number>'
    r'(?P<numerator>\d+(\.\d+)?)'
    r'(/(?P<denominator>\d+))?)'
    r'(\s*(?P<unit>\w+(?:/\w+)?))?\s*$'
)


# This is largely based on units and other conversion tool, but made
#  much simpler for this need with the added feature that all units
#  store value as is - and are referenced from the smallest unit.
# Also, the __call__ was overriden to make things easy to use and read:
# a = 4*mm can be written as a = mm(4)
# Accessing the value of a is simply a() - or in um say : a(um).
# Array can be created with the correct unit - so thou, inch and mm can be
#  mixed without loss of precision and working on integers
class Quantity:
    """
    Represents the quantity of a given unit
    """
    def __init__(self, value, base_unit):
        """
        Construct the quantity from:
            - a string of ints, floats and fractions
            - a integer or a float
            - a quantity
            and a unit
        Try to keep the number as integer
        """
        # A string representing the value passed in. A fraction would be stored as a fraction
        self._raw = None

        if isinstance(value, str):
            m = RE_NUMBER.match(value)
            n = m.group("numerator")
            d = m.group("denominator")

            # Convert to number
            n = float(n) if '.' in n else int(n)
            d = int(d) if d else 0
            self._value = n/d if d else n

            self._raw = m.group("number")
        elif isinstance(value, Quantity):
            assert(value.base_unit.__type__ == base_unit.__type__)
            self._value = value(base_unit)
            self._raw = str(self._value)
        else:
            self._value = value
            self._raw = str(value)

        # Bares the Unit type
        self.base_unit = base_unit

    def __call__(self, target_unit=None):
        if target_unit is None:
            return self._value
        else:
            retval = self._value * self.base_unit.conversion_to(target_unit)

            if int(retval) == retval:
                return int(retval)

            # Loose some precision to avoid rounding errors
            return fround(retval)

    @property
    def value(self):
        return self._value

    @property
    def base(self):
        """
        Return the base unit value
        The internal value is mutliplied by the convertion factor
        """
        return self._value * self.base_unit.conversion_factor

    @property
    def unit(self):
        return self.base_unit

    def __mul__(self, other):
        if isinstance(other, (int, float, complex)):
            return Quantity(self.value * other, self.base_unit)
        elif isinstance(other, list):
            return [item * self for item in other]
        else:
            raise TypeError("Unsupported multiplication type")

    def __truediv__(self, other):
        if isinstance(other, (int, float, complex)):
            return Quantity(self.value / other, self.base_unit)
        elif isinstance(other, list):
            return [item / self for item in other]
        else:
            raise TypeError("Unsupported division type")

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return self.__div__(other)

    def __add__(self, other):
        if isinstance(other, Quantity):
            other_value = other(self.base_unit)
        else:
            other_value = other
        return Quantity(self._value + other_value, self.base_unit)

    def __sub__(self, other):
        if isinstance(other, Quantity):
            other_value = other(self.base_unit)
        else:
            other_value = other
        return Quantity(self._value - other_value, self.base_unit)

    def __abs__(self):
        return Quantity(abs(self._value), self.base_unit)

    def __repr__(self):
        return f"{self._raw}{self.base_unit.name}"

    def __apply_operator(self, other, operator):
        if isinstance(other, (int, float)):
            return operator(self.value, other)
        elif isinstance(other, Quantity):
            converted_other = other(self.base_unit)
            return operator(fround(self.value), converted_other)
        else:
            raise TypeError("Unsupported operation type")

    def __lt__(self, other):
        return self.__apply_operator(other, __lt__)

    def __le__(self, other):
        return self.__apply_operator(other, __le__)

    def __eq__(self, other):
        return self.__apply_operator(other, __eq__)

    def __ne__(self, other):
        return self.__apply_operator(other, __ne__)

    def __ge__(self, other):
        return self.__apply_operator(other, __ge__)

    def __gt__(self, other):
        return self.__apply_operator(other, __gt__)

    def __hash__(self):
        """
        Convert to the smallest
        """
        return hash(self.value * self.base_unit.conversion_factor)


class Unit:
    """
    Represents the unit used by the Quantity
    """
    __types__ = {}
    __units__ = {}
    __type__ = None
    __default__ = None

    def __init__(self, name, conversion_factor):
        self.name = name
        self.conversion_factor = conversion_factor
        __class__.__units__[name] = self

    def __call__(self, value=None):
        return Quantity(value, self)

    @classmethod
    @property
    def type(cls):
        """
        @return The type (as a class of this unit)
        """
        return cls.__types__[cls.__type__]

    @staticmethod
    def get_type(type_str):
        """
        Get the unit type (base class) from a type string description

        @param type_str The type string
        @returns The type from the unit str. So 'mm' will return Length etc.
        """
        return __class__.__types__[type_str]

    @staticmethod
    def get_unit(unit_str):
        """
        Factory method to get a Unit object from a string
        @returns The unit object
        """
        return __class__.__units__[unit_str]

    def conversion_to(self, other_unit):
        """
        Converts to another unit
        """
        assert(other_unit.__type__ == self.__type__)

        if self.conversion_factor % other_unit.conversion_factor == 0:
            return int(self.conversion_factor / other_unit.conversion_factor)
        else:
            return self.conversion_factor / other_unit.conversion_factor

    def __rmul__(self, other):
        if isinstance(other, (int, float, complex)):
            return Quantity(other, self)
        elif isinstance(other, list):
            return [Quantity(item, self) for item in other]
        else:
            raise TypeError("Unsupported multiplication type")

    @classmethod
    def from_string(cls, value, default_unit=None):
        # All numbers are as n/d
        # Scan the units and try
        unit_type = cls.__type__
        assert(unit_type is not None)
        match = RE_NUMBER.match(value)
        assert(match)

        # Grab the unit string
        unit = match.group("unit")

        if not unit:
            if default_unit:
                unit = default_unit
            else:
                # Use the type default
                unit = cls.__default__

        # Look for the unit object
        assert(unit in cls.__units__)

        return Quantity(match.group("number"), cls.__units__[unit])

    @classmethod
    def from_scalar(cls, value):
        assert(cls.__type__ is not None)
        unit = cls.__default__
        assert(unit in cls.__units__)
        return Quantity(value, cls.__units__[unit])


def register_unit_type(name):
    """ Decorator to register unit types """
    def decorator(cls):
        Unit.__types__[name] = cls
        cls.__type__ = name
        return cls
    return decorator

@register_unit_type("length")
class Length(Unit):
    __default__ = "mm"

@register_unit_type("feedrate")
class FeedRate(Unit):
    __default__ = "mm/min"

@register_unit_type("angle")
class Angle(Unit):
    __default__ = "degree"

@register_unit_type("rpm")
class Rpm(Unit):
    __default__ = "rpm"

# Define unit objects
um = Length("um", 1)
mm = Length("mm", 1000)
cm = Length("cm", 10000)
mil = Length("mil", 25.4)
thou = Length("thou", 25.4)
inch = Length("inch", 25400)
_in = Length("in", 25400)

# Define feedrate units
mm_min = FeedRate("mm/min", 1)
cm_min = FeedRate("cm/min", 10)
m_min = FeedRate("m/min", 100)
in_min = FeedRate("in/min", 25.4)
ipm = FeedRate("ipm", 25.4)
inch_min = FeedRate("inch/min", 25.4)

# Define angles
deg = Angle("deg", 1)
degree = Angle("degree", 1)

# Define rotational speed units
rpm = Rpm("rpm", 1)
