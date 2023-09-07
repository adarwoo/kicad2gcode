from pathlib import Path
from pcb2gcode.board_processor import BoardProcessor

def test_simple_file():
   # Load from this folder
   this_path = Path(__file__).resolve().parent
   pcb_file_path = this_path / "pulsegen.kicad_pcb"

   b = BoardProcessor(pcb_file_path)
   i = b.generate_inventory()
   print(i)