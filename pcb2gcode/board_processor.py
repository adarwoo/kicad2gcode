"""
Process a board in order to create an inventory
"""
from pathlib import Path
from .rack import RackManager, Rack
from .units import Length
from .pcb_inventory import Inventory

from kiutils.board import Board

from kiutils.items.brditems import Via, Segment
from kiutils.items.common import Position

class BoardProcessor:
   def __init__(self, pcb_file_path):
      self.inventory = Inventory()
      board = Board.from_file(pcb_file_path)

      self._process(board)

   def _process(board):
      # Scan all traces to find pads
      for footprint in board.footprints:
         pos = footprint.position
         for pad in footprint.pads:


      # Scan all vias

      # Scan all routing

 def __init__(self, board):
        from pcbnew import PCB_VIA_T

        self.holes = list() # type: List[Hole]
        self.routing_segments = []

        # Start with the pads
        self.process_pads(board.GetPads())
        self.process_vias([t for t in board.GetTracks() if t.Type() == PCB_VIA_T])

        # Work out the offset
        self.offset = board.GetDesignSettings().GetAuxOrigin()

    def process_pads(self, pads):
        from pcbnew import PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH, PAD_DRILL_SHAPE_CIRCLE, \
        PAD_DRILL_SHAPE_OBLONG

        for pad in pads:
            # Check for pads where drilling or routing is required
            pad_attr = pad.GetAttribute()

            if pad_attr in [PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH]:
                pos = pad.GetPosition()
                size_x = pad.GetDrillSizeX()
                size_y = pad.GetDrillSizeY()

                # Drill or route?
                if (pad.GetDrillShape() == PAD_DRILL_SHAPE_CIRCLE) or (size_x == size_y):
                    self.holes.append(
                        Hole(pad.GetDrillSizeX(), pos[0], pos[1], pad_attr == PAD_ATTRIB_PTH)
                    )
                elif pad.GetDrillShape() == PAD_DRILL_SHAPE_OBLONG:
                    # Oblong pad location is the center
                    # X and Y sizes, with the orientation gives the start hole and end
                    orientation_degree = pad.GetOrientationDegrees()

                    # Determine the orientation
                    # WARNING : As KiCad uses screen coordinates, angles are inverted
                    hole_width = min(size_x, size_y)
                    radius = (max(size_x, size_y) - hole_width) / 2
                    angle = radians((90 if size_x < size_y else 0) - orientation_degree)
                    dx = radius * cos(angle)
                    dy = radius * sin(angle)
                    x1, y1 = (pos[0] + dx, pos[1] + dy)
                    x2, y2 = (pos[0] - dx, pos[1] - dy)

                    # Append an oblong hole
                    self.holes.append(
                        Oblong(hole_width, x1, y1, x2, y2, pad_attr == PAD_ATTRIB_PTH)
                    )

    def process_vias(self, vias):
        from pcbnew import VIATYPE_THROUGH

        for via in vias:
            hole_sz = via.GetDrillValue()

            # Must have a hole!
            if hole_sz == 0:
                continue

            if via.GetViaType() != VIATYPE_THROUGH:
                # We don't support burried vias
                continue

            # Check the via is through - discard other holes
            x, y = via.GetStart()

            self.holes.append(
                Hole(via.GetDrillValue(), x, y)
            )