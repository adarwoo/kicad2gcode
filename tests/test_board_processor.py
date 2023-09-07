from pathlib import Path
from pcb2gcode.board_processor import BoardProcessor

from pcb2gcode.units import mm


def test_simple_file():
   # Load from this folder
   this_path = Path(__file__).resolve().parent
   pcb_file_path = this_path / "pulsegen.kicad_pcb"

   b = BoardProcessor(pcb_file_path)
   
   assert len(b.inventory.pth) > 0
   assert len(b.inventory.npth) > 0
   
   for dia, holes in b.inventory.pth.items():
      print(dia, holes)
      print(dia(mm), len(holes) )