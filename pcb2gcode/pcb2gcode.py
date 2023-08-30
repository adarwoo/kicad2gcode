#!/usr/bin/python3

__author__ = "guillaume arreckx"
__copyright__ = "Copyright 2023, ARex"
__license__ = "GPL"
__version__ = 3.1
__email__ = "software@arreckx.com"

"""
Example file to convert a PCB to gcode
Note : Work in progress
"""
import pcbnew

from pathlib import Path

from inventory import Inventory
from machining import Machining, MachiningWhat
from rack import RackManager, Rack

# Load from this folder
this_path = Path(__file__).resolve().parent
pcb_file_path = this_path.parent / "pulsegen/pulsegen.kicad_pcb"
board = pcbnew.LoadBoard(str(pcb_file_path))

# Load the rack configuration
rack_manager = RackManager()
current_rack = RackManager.get_rack()

# Create an inventory of all things which could be machined in the PCB
inventory = Inventory(board)

# Create an object to machine PTH only
machining = Machining(inventory)

# Grab the rack
required_rack = machining.create_tool_rack(MachiningWhat.DRILL_PTH)
current_rack.merge(required_rack)

# What does the operator needs to do?
rack_ops = required_rack.diff(current_rack)
print(rack_ops)

# Generate the GCode
gcode = machining.gcode(MachiningWhat.DRILL_PTH)

print(gcode)
