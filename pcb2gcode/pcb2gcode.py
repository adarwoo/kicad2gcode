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
Entry module for the package.
Provides the command line tool.
"""
import sys
import click

from .machining import Machining, Operations
from .board_processor import BoardProcessor
from .rack import RackManager


@click.command()
@click.option(
   '-p', '--pth', is_flag=True, default=False,
   help='Drill and route all requiring plating.')
@click.option(
   '-n', '--npth', is_flag=True, default=False,
   help='Final drills and route and non-plated features')
@click.option(
   '-l', '--outline', is_flag=True, default=False,
   help='Route the PCB outiline')
@click.option(
   '-a', '--all', is_flag=True,
   default=False, help='Do all operations')
@click.option(
   '-o', '--output', type=click.File("wt"), default=sys.stdout,
   help='Specify an output file name. Defaults to stdout')
@click.argument('filename', type=click.Path(exists=True, readable=True))
@click.pass_context
def pcb2gcode(*_, **kwargs):
   """
   A utility which take a KiCAD v7 PCB and creates the GCode
   for a CNC to drill and route the PCB.
   The utility is heavily configurable. The initial set of configuration files
   is create the first time the utility runs.
   You can then edit them. The default path is ~/.pcb2gcode.
   """
   ops = Operations.NONE

   # Object responsible for managing the rack. Loads the configured rack
   rack_manager = RackManager()
   rack = rack_manager.get_rack()

   # Get the requested operations
   if kwargs['pth']:
      ops |= Operations.PTH

   if kwargs['npth']:
      ops |= Operations.NPTH

   if kwargs['outline']:
      ops |= Operations.OUTLINE

   if kwargs['all']:
      ops = Operations.ALL

   if ops is Operations.NONE:
      click.echo("Nothing to do. Check options to turn on features.")
      sys.exit(0)

   # Get the inventory using the board_processor
   processor = BoardProcessor(kwargs['filename'])

   # Create a machining object for our operations
   machining = Machining(processor.inventory)

   # Process the inventory for the given operations
   required_rack = machining.process(ops)

   # Merge the required rack with the configured rack
   rack_handling_ops = rack.merge(required_rack)

   # Let the user know what to do
   if not rack.is_manual:
      click.echo("Rack configuration:")

      for rack_op in rack_handling_ops:
         click.echo(f"In T{rack_op.slot}: {rack_op.name} -> {rack_op.final_tool}")

   # Prepare the code generating by forcing the new rack
   machining.use_rack(rack)

   # Optimize all displacements
   machining.optimize()

   # Generate the GCode
   machining.generate_machine_code(kwargs["output"])


if __name__ == '__main__':
    pcb2gcode()
