import sys
from pathlib import Path
from pcb2gcode.board_processor import BoardProcessor
from pcb2gcode.machining import Machining
from pcb2gcode.operations import Operations

from pcb2gcode.units import mm


def test_simple_file():
   # Load from this folder
   this_path = Path(__file__).resolve().parent
   pcb_file_path = this_path / "pulsegen.kicad_pcb"

   processor = BoardProcessor(pcb_file_path)
   
   for dia, holes in processor.inventory.pth.items():
      print(dia, holes)
      print(dia(mm), len(holes) )   

   for dia, holes in processor.inventory.npth.items():
      print(dia, holes)
      print(dia(mm), len(holes) )   
   
   # Create a machining object for our operations
   machining = Machining(processor.inventory)
   
   # Process the inventory for the given operations
   required_rack = machining.process(Operations.ALL)
   
   print(required_rack)
   
   # Optimize all displacements
   machining.optimize()

   # Generate the GCode
   machining.generate_machine_code(sys.stdout)
  
