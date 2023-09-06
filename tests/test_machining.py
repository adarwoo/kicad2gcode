from pathlib import Path

#from pcb2gcode.pcb_inventory import Inventory
#from pcb2gcode.machining import Machining, Operations
from pcb2gcode.rack import RackManager, Rack

from kiutils.board import Board
from kiutils.items.brditems import Via, Segment
from kiutils.items.common import Position

this_path = Path('.')
pcb_file_path = this_path / "pulsegen.kicad_pcb"
b = Board.from_file(pcb_file_path)


def test_board():

   b = Board.from_file(pcb_file_path)

   dir(b)
   for pad in b.traceItems:
      print(pad)