"""
Process a board in order to create an inventory
"""
from pathlib import Path
from logging import getLogger

from .rack import RackManager, Rack
from .units import Length
from .pcb_inventory import Inventory

logger = getLogger(__name__)

def append_path():
   import platform
   import sys

   if platform.system() == "Windows":
      try:
         import winreg

         # We need to add KiCad to the path
         location = winreg.HKEY_LOCAL_MACHINE
         key = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\KiCad 7.0"
         value = 'InstallLocation'

         kicad_keytype = winreg.OpenKeyEx(location, key)
         path_to_kicad = Path(winreg.QueryValueEx(kicad_keytype, value)[0]).absolute()

         # Create the path to append to sys
         for path in [
            'bin/DLLs', 'bin/Lib', 'bin/Lib/site-packages', 'bin']:
            full_path = path_to_kicad / path

            # Import all from sys.path as Path object for proper compare
            sys_paths = [Path(p).absolute() for p in sys.path]

            if full_path not in sys_paths:
               sys.path.append(str(full_path))

         # OS path needs updating too to locate the _pcbnew.dll
         import os
         os.environ['PATH'] = str(path_to_kicad / "bin") + os.pathsep + os.environ['PATH']
         print("PYTHJPATH", sys.path)
         print("PATH", os.environ['PATH'])
         import pcbnew
      except Exception as exception:
         logger.fatal("Cannot locate KiCad on the system")
         logger.info("Got: {}", exception)
         print(exception)
   else:
      # TODO
      pass

try:
   append_path()
   print("XXXXXXXXXXXXXXXXXXXXX", )
   from pcbnew import LoadBoard, BOARD, PCB_VIA_T, VIATYPE_THROUGH, \
      PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH, PAD_DRILL_SHAPE_CIRCLE, PAD_DRILL_SHAPE_OBLONG
except:
   raise RuntimeError("Failed to import pcbnew")


class BoardProcessor:
   def __init__(self, pcb_file_path):
      LoadBoard(pcb_file_path)

      self.inventory = Inventory()

      # Start with the pads
#      self.process_pads(board.GetPads())
#      self.process_vias([t for t in board.GetTracks() if t.Type() == PCB_VIA_T])

#      # Work out the offset
#      self.offset = board.GetDesignSettings().GetAuxOrigin()

#  def process_pads(self, pads):

#      for pad in pads:
#          # Check for pads where drilling or routing is required
#          pad_attr = pad.GetAttribute()

#          if pad_attr in [PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH]:
#              pos = pad.GetPosition()
#              size_x = pad.GetDrillSizeX()
#              size_y = pad.GetDrillSizeY()

#              # Drill or route?
#              if (pad.GetDrillShape() == PAD_DRILL_SHAPE_CIRCLE) or (size_x == size_y):
#                  self.holes.append(
#                      Hole(pad.GetDrillSizeX(), pos[0], pos[1], pad_attr == PAD_ATTRIB_PTH)
#                  )
#              elif pad.GetDrillShape() == PAD_DRILL_SHAPE_OBLONG:
#                  # Oblong pad location is the center
#                  # X and Y sizes, with the orientation gives the start hole and end
#                  orientation_degree = pad.GetOrientationDegrees()

#                  # Determine the orientation
#                  # WARNING : As KiCad uses screen coordinates, angles are inverted
#                  hole_width = min(size_x, size_y)
#                  radius = (max(size_x, size_y) - hole_width) / 2
#                  angle = radians((90 if size_x < size_y else 0) - orientation_degree)
#                  dx = radius * cos(angle)
#                  dy = radius * sin(angle)
#                  x1, y1 = (pos[0] + dx, pos[1] + dy)
#                  x2, y2 = (pos[0] - dx, pos[1] - dy)

#                  # Append an oblong hole
#                  self.holes.append(
#                      Oblong(hole_width, x1, y1, x2, y2, pad_attr == PAD_ATTRIB_PTH)
#                  )

#  def process_vias(self, vias):

#      for via in vias:
#          hole_sz = via.GetDrillValue()

#          # Must have a hole!
#          if hole_sz == 0:
#              continue

#          if via.GetViaType() != VIATYPE_THROUGH:
#              # We don't support burried vias
#              continue

#          # Check the via is through - discard other holes
#          x, y = via.GetStart()

#          self.holes.append(
#              Hole(via.GetDrillValue(), x, y)
#          )

