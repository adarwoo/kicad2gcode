#!/usr/bin/python3

from units import unit, scaled_unit
from units.quantity import Quantity

um=unit('um')
mm=scaled_unit('mm', 'um', 1000)
mil=scaled_unit('mil', 'um', 2.54)
inch=scaled_unit('in', 'mil', 1000)

def as_mm(quantity: Quantity):
    return mm(quantity).num

if __name__ == "__main__":
    a = mm(4)
    b = um(300)
    c = mil(1000)

    print(a,b,c)
