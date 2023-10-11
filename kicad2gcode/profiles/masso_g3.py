from time import strftime

from kicad2gcode.cutting_tools import CutDir, CuttingTool
from kicad2gcode.units import Length, FeedRate, Rpm, mm, mm_min
from kicad2gcode.context import ctx


def header():
    """
    Called to create the header of the gcode file
    """
    yield f"""
        (Created by kicad2gcode from '{ctx.pcb_filename}' - {strftime("%Y-%m-%d %H:%M:%S")})
        (Reset all back to safe defaults)
        G17 G54 G40 G49 G80 G90
        G21
        G10 P0
        (Establish the Z-Safe)
        G0 Z{ctx.gs.z_safe_height(mm)}
    """

def footer():
    """
    Last chance to reset things at the end of the cycle
    """
    yield "(end of file)"


def drill_hole(
    x: Length, y: Length,
    z_feedrate: FeedRate,
    z_retract: Length,
    z_bottom: Length,
    index,
    last_index):
    """
    Generate the GCode to drill one hole from many.
    The hole index is given, so a canned cycle can be used.

    Variables are:
        x, y:       Center location of the hole as lengths
        z_feedrate: Optimimum feedrate drilling in
        z_retract:  Height to retract to between drills
        z_bottom:   Minimum height to reach during the drilling. Do not go any deeper.
        index:      Number (0 based) of the hole in the series
        last_index: Index of the last hole in the serie.
    """
    if index == 0:
        # Move fast to first hole position - Move Z first to avoid collisions
        yield f"G0 X{x(mm)} Y{y(mm)} Z{ctx.gs.z_safe_height(mm)}"

        # Turn spindle on once over the first hole
        # That way we get a change to stop is the position is way off

        # Set the retract to drill height if there other holes
        yield "G98" if last_index == index else "G99"

        # Start the drill can cycle
        yield f"G81 Z{z_bottom(mm)} R{z_retract(mm)} F{z_feedrate(mm_min)}"
    else:
        # Move to the next hole
        yield f"X{x(mm)} Y{y(mm)}"

    # If the hole was the last, cancel the can cycle
    if last_index == index:
        yield "G80"


def route_hole(
    size: Length,
    x: Length, y: Length,
    d: Length,
    cutdir: CutDir,
    feedrate: FeedRate,
    z_feedrate: FeedRate,
    z_safe: Length,
    z_bottom: Length):
    """
    Called to generate the GCode for cutting a hole with a router bit
    Note: When you route the hole in a clockwise direction (viewed from above)
     with an upcut bit, it tends to pull the chips up and out of the hole.
    This results in a cleaner top surface at the expense of the bottom - which
    should not happen if the backboard does its job
    Note: Z0 is set to the machine bed, that is the bottom of the backing board
           Doing so, allow zero setup of the Z0, and the board thickness information
           is not required

    Variables are:
        size:       Diameter of the hole as a length. Convert appropriatly
        x, y:       Center location of the hole as lengths
        d:          Diameter of the cutter
        cutdir:     Up of down or updown cutter type
        feedrate:   Lateral displacement feedrate
        z_feedrate: Z feedrate
        z_safe:     Z to retract to
        z_bottom:   Depth to go to

    Yields:
        The g-code text
    """
    id = (size - d) / 2

    # Go straight down in the center
    yield f"""G90 G0 X{x(mm)} Y{y(mm)}
    G1 Z{z_bottom(mm)} F{z_feedrate(mm_min)}
    G1 Y{(y+id)(mm)}
    """

    if cutdir in [CutDir.UP, CutDir.UPDOWN]:
        yield f"""G2 I0 J-{id(mm)}"""
    else:
        yield f"""G3 I0 J-{id(mm)}"""

    yield f"""G0 Z{z_safe(mm)}"""


def change_tool(slot: int, tool: CuttingTool):
    """
    GCode for tool change.
      Variables are:
        slot:     holds the tool slot number
        tool:     Tool object
    """
    msg = f"""
        MSG Load {tool.name} {tool.diameter}
        M01
    """ if ctx.rack.is_manual else ""


    yield f"""
        M05
        {msg}
        T{slot} M06
        S{tool.rpm()}
    """
