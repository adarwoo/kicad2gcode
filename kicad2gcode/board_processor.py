# -*- coding: utf-8 -*-

#
# This file is part of the kicad2gcode distribution (https://github.com/adarwoo/kicad2gcode).
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
Process a board in order to create an inventory
All KiCAD coordinate and positions are converter here

This should be the only file with dependencies to the KiCAD libary.
No KiCAD is exposed outside of this file
"""
import platform
import sys

from pathlib import Path
from logging import getLogger

from .coordinate import Coordinate
from .units import nm, degree
from .pcb_inventory import Inventory


logger = getLogger(__name__)

# Import pcbnew from Linux or Windows.
try:
    if platform.system() == "Windows":
        try:
            # pylint: disable=E0401 # Only in windows
            import winreg

            # We need to add KiCad to the path
            location = winreg.HKEY_LOCAL_MACHINE
            KEY = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\KiCad 7.0"
            VALUE = 'InstallLocation'

            kicad_keytype = winreg.OpenKeyEx(location, KEY)
            path_to_kicad = Path(winreg.QueryValueEx(
                kicad_keytype, VALUE)[0]).absolute()

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
            os.environ['PATH'] = str(
                path_to_kicad / "bin") + os.pathsep + os.environ['PATH']
            print("PYTHJPATH", sys.path)
            print("PATH", os.environ['PATH'])
        except Exception as exception:
            logger.fatal("Cannot locate KiCad on the system")
            logger.info("Got: '%s'", exception)
            print(exception)
    else:
        # Python case
        from .constants import THIS_PATH
        import os

        kicad = THIS_PATH / "pcbnew"
        os.environ["LD_LIBRARY_PATH"] = str(
            kicad) + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
        sys.path.append(str(kicad))

    from pcbnew import LoadBoard, BOARD, PCB_VIA_T, VIATYPE_THROUGH, \
        PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH, PAD_DRILL_SHAPE_CIRCLE, PAD_DRILL_SHAPE_OBLONG
except:
    raise RuntimeError("Failed to import pcbnew")


def tocoord(x, y):
    """ @return A traditional coordinate given in Units """
    return Coordinate(
        nm(x - tocoord.offset.x),
        nm(tocoord.offset.y - y)
    )


class BoardProcessor:
    """ Process a KiCAD PCB board """

    def __init__(self, pcb_file_path):
        from .context import ctx

        board = LoadBoard(pcb_file_path)
        ctx.pcb_filename = pcb_file_path

        self.inventory = Inventory()

        # Work out the bounding box
        bounding_box = board.ComputeBoundingBox()
        tocoord.offset = bounding_box.GetPosition()
        tocoord.offset.x = bounding_box.GetLeft()
        tocoord.offset.y = bounding_box.GetBottom()

        # Work out the offset (in KiCAD coordinates)

        # Store the number of copper layers in the context
        ctx.copper_layer_count = board.GetCopperLayerCount()

        # Start with the pads
        self.process_pads(board.GetPads())

        # Then vias
        self.process_vias(
            [t for t in board.GetTracks() if t.Type() == PCB_VIA_T])

        # Finally - for now - contours
        self.process_edge_shapes(board.GetDrawings())

    def process_pads(self, pads):
        """ Grab all pads from all footprints and add to the inventory """
        for pad in pads:
            # Check for pads where drilling or routing is required
            pad_attr = pad.GetAttribute()

            if pad_attr in [PAD_ATTRIB_PTH, PAD_ATTRIB_NPTH]:
                pos = pad.GetPosition()
                coord = tocoord(pos[0], pos[1])
                angle = degree(pad.GetOrientationDegrees())
                size_x = nm(pad.GetDrillSizeX())
                size_y = nm(pad.GetDrillSizeY())
                pth = (pad_attr == PAD_ATTRIB_PTH)

                # Drill or route?
                self.inventory.add_hole(
                    coord, size_x, size_y=size_y, angle=angle, pth=pth)

    def process_vias(self, vias):
        """ Grab all vias and add to inventory """
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

            self.inventory.add_hole(tocoord(x, y), nm(hole_sz))

    def process_edge_shapes(self, shapes):
        """ Grab all edge drawing elements """
        for shape in shapes:
            if shape.GetLayerName() == "Edge.Cuts":
                shape_type = shape.SHAPE_T_asString()

                if shape_type == "S_ARC":
                    self.append_arc(shape)
                elif shape_type == "S_SEGMENT":
                    self.append_segment(shape)
                elif shape_type == "S_CIRCLE":
                    self.append_circle(shape)
                else:
                    logger.error("Not supported yet - work in progress")

    def append_segment(self, segment):
        start = segment.GetStart()
        end = segment.GetEnd()
        logger.debug(f"Segment: {start}, {end}")

    def append_arc(self, arc):
        angle = arc.GetArcAngle().AsDegrees()
        centre = arc.GetCenter()
        diameter = arc.GetRadius() * 2
        logger.debug(f"Arc: {angle}, {centre}, {diameter}")

    def append_circle(self, circle):
        start = circle.GetStart()
        diameter = circle.GetRadius() * 2
        logger.debug(f"Circle: {start}, {diameter}")
