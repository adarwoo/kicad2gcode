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
from pathlib import Path

from .pcb_inventory import Inventory
from .machining import Machining, Operations
from .rack import RackManager, Rack
from .board_processor import BoardProcessor

import click

@click.command()
@click.option(
   '-p', '--pth', is_flag=True, default=False,
   help='Drill and route all requiring plating.')
@click.option(
   '-n', '--npth', is_flag=True, default=False,
   help='Final drills and route and non-plated features')
@click.option(
   '-l', '--outline', is_flag=True,
   default=False, help='Route the PCB outiline')
@click.option(
   '-a', '--all', is_flag=True,
   default=False, help='Do all operations')
@click.option(
   '-o', help='Specify an output file name')
@click.argument('filename', type=click.Path(exist=True, readable=True),
   help="File to process")
@click.pass_context
def pcb2gcode(ctx, *args, **kwargs):
   # Get the inventory using the board_processor
   processor = BoardProcessor(args[0])
   inventory = processor.inventory

   # Get the operations
   ops = Operations.PTH if kwargs['pth']
   ops |= Operations.PTH if kwargs['npth']
   ops |= Operations.OUTLINE if kwargs['route']

   # Load the rack configuration
   rack_manager = RackManager()
   current_rack = RackManager.get_rack()

   # Create an object to machine PTH only
   machining = Machining(inventory, ops)

   # Grab the rack
   required_rack = machining.create_tool_rack()
   current_rack.merge(required_rack)

   # What does the operator needs to do?
   rack_ops = required_rack.diff(current_rack)

   # Generate the GCode
   gcode = machining.gcode()

   kwargs['output'].write(gcode)


if __name__ == '__main__':
    pcb2gcode()
