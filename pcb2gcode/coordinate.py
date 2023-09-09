# -*- coding: utf-8 -*-

#
# This file is part of the pcb2gcode distribution (https://github.com/adarwoo/pcb2gcode).
# Copyright (c) 2023 Guillaume ARRECKX (software@arreckx.com).
# 
# This program is free software: you can redistribute it and/or modify  
# it under the terms of the GNU General Public License as published by  
# the Free Software Foundation, version 3.
#
# This program is distributed in the hope that it will be useful, but 
# WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU 
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License 
# along with this program. If not, see <http://www.gnu.org/licenses/>.
#
""" 
A coordinate system using Length quantities.
This class is a place holder for specific operations required by this application
such as return a numpy array for the TSP algorithm.
"""
from typing import Tuple
from numpy import array

from .units import Length


class Coordinate:
    """
    Helper object to store coordinates which could be visited
    to be later rendered using different offset and scale.
    """
    def __init__(self, x: Length, y: Length):
        """ Construct using int """
        self.x = x
        self.y = y

    def __array__(self):
        """ @return a numpy array using the base unit conversion """
        return array([self.x.base, self.y.base])
    
    def __call__(self) -> Tuple[int, int]:
        return [self.x.base, self.y.base]
