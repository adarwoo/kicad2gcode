#!/usr/bin/python3

# This is largely based on units and other conversion tool, but made
#  much simpler for this need with the added feature that all units
#  store value as is - and are referenced from the smallest unit um.
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
        self._value = value
        self.base_unit = base_unit

    def __call__(self, target_unit=None):
        if target_unit is None:
            return self._value
        else:
            return self._value * self.base_unit.conversion_to(target_unit)
        
    @property
    def value(self):
        return self._value

    def __mul__(self, other):
        if isinstance(other, (int, float, complex)):
            return Quantity(self.value * other, self.base_unit)
        elif isinstance(other, list):
            return [item * self for item in other]
        else:
            raise TypeError("Unsupported multiplication type")    

    def __rmul__(self, other):
        return self.__mul__(other)
    
    def __add__(self, other):
        if isinstance(other, Quantity):
            other_value = other(self.base_unit)
        else:
            other_value = other
        return Quantity(self._value + other_value, self.base_unit)

    def __repr__(self):
        return f"{self._value}{self.base_unit.name}"


class Unit:
    """
    Represents the unit used by the Quantity
    """
    def __init__(self, name, conversion_factor):
        self.name = name
        self.conversion_factor = conversion_factor

    def __call__(self, value=None):
        return Quantity(value, self)

    def conversion_to(self, other_unit):
        return self.conversion_factor / other_unit.conversion_factor

    def __rmul__(self, other):
        if isinstance(other, (int, float, complex)):
            return Quantity(other, self)
        elif isinstance(other, list):
            return [Quantity(item, self) for item in other]
        else:
            raise TypeError("Unsupported multiplication type")    


# Define unit objects
um = Unit("um", 1)
mm = Unit("mm", 1000)
mil = Unit("mil", 25.4)
thou = Unit("thou", 25.4)
inch = Unit("inch", 25400)


if __name__ == "__main__":
    aa = mm(5)
    print(aa)
    a = 4 * mm
    print(a())  # Output: 4
    print(a(mil))  # Output: 1016
    print(a(um))  # Output: 4000
    c = a + 3000*um
    print(c)  # Output: 7 mm

    # Example
    a = 4 * mm
    b = [3, 4, 6] * mm
    print(a)  # Output: 4 mm
    print(b)  # Output: [3 mm, 4 mm, 6 mm]
