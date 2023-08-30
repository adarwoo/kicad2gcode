#!/usr/bin/python3

# Rack management for the project
# If the CNC has automated changes, you want to create a standard
# rack, so most jobs will reuse the same tool position
# Can also be used to compute the wear of the bits in the rack

# Complex number are used where real part is a drill bit and the imaginary a router

from pathlib import Path
from typing import Self
from math import tan, radians
from collections import OrderedDict

from settings import *
from utils import *

import yaml
import jsonschema
import logging
import os


# Constants
THIS_PATH = Path(__file__).parent
RACK_SCHEMA_FILE = THIS_PATH / "rack_schema.json"
TEMPLATE_RACK_FILE = THIS_PATH / "default_rack_template.yaml"
RACK_FILE = Path(os.path.expanduser(RACK_FILE_PATH))

# Multiple the diameter by this number to find the length of the tip of the bit
HEIGHT_TO_DIA_RATIO = tan(radians((180-DRILLBIT_POINT_ANGLE)/2))

# Compute the largest drillbit size where there is enough clearance in the backing board for
#  the point to exit cleanly
MAX_DRILLBIT_DIAMETER_FOR_CLEAN_EXIT = \
    int(MAX_DEPTH_INTO_BACKBOARD - MIN_EXIT_DEPTH) / HEIGHT_TO_DIA_RATIO

logger = logging.getLogger(__name__)


class Rack:
    """
    Defines a rack object which behaves like a map where the key is the diameter,
    and an array which maps the rack physically and has a size
    """
    def __init__(self, size=0):
        """
        Construct a rack.
        @param size The initial size of the rack. If size is 0, the rack is not
                    size bound.
        """
        self.rack = [None] * size
        self.size = size

    def __getitem__(self, key):
        return self.rack[key - 1]

    def __setitem__(self, key, value):
        self.rack[key - 1] = value

    def __delitem__(self, key):
        del self.rack[key - 1]

    def __contains__(self, key):
        return key in self.keys()

    def __len__(self):
        return len(self.rack)

    def clone(self, unbound=True):
        """ @returns A deep copy of the rack, unbound in size """
        from copy import deepcopy

        retval = type(self)(self.size if not unbound else 0)
        retval.rack = deepcopy(self.rack)

        return retval

    def items(self):
        return [(bit, i) for i, bit in enumerate(self.rack, start=1)]

    def keys(self):
        return self.rack

    def values(self):
        return list(range(1, len(self.rack) + 1))

    def get_tool(self, slot):
        """ @return The tool diameter in the given T slot or None """
        if slot < 1 or slot > len(self.rack):
            return None

        return self.rack[slot-1]

    def find_nearest_drillbit_size(self, dia):
        """
        Request a diameter from the rack.
        If a suitable bit already exists (or a matching diameter), return the tool number

        @param The diameter as a float(mm) or int(um)
        @returns The tool number of None
        """
        return find_nearest_drillbit_size(TO_MM(dia), self.keys())

    def add_bit(self, bit, position=None):
        """
        Add the bit to the rack.
        """
        if position is None:
            position = self.find_free_position()
        elif position < 1 or position > len(self.rack):
            raise ValueError("Invalid position")

        if self.rack[position - 1] is not None:
            logger.warning(
                f"Warning: Slot {position} already occupied with "
                "{self.rack[position - 1]}"
            )

        # Chech if the same diameter is not already occupied
        for dia, slot in self.items():
            if TO_MM(bit) == dia:
                logger.warning(
                    f"Warning: Bit {DIA_TO_STR(dia)}mm in T{position:02} "
                    "is already present in the rack at T{slot:02}. "
                    "This slot will not be used."
                )

        self.rack[position - 1] = bit

    def request(self, diameter):
        """
        Requests a drill bit from the rack from the standard size
        Try to reuse an existing bit, otherwise, add a new one
        from the standard sizes.
        """
        retval = self.find_nearest_drillbit_size(diameter)

        if not retval:
            # Get a standard size bit
            retval = find_nearest_drillbit_size(diameter)

            # Make sure the bit geometry is compatible with the backing board thickness
            if retval and TO_MM(retval) > MAX_DRILLBIT_DIAMETER_FOR_CLEAN_EXIT:
                # If not found or too deep - the hole must be routed
                # - but let's drill the largest hole first
                # But to do so - since the router dia can be any smaller size
                # - we need to wait for the drill rack to be completed
                exit_depth_required = HEIGHT_TO_DIA_RATIO * TO_MM(retval) + MIN_EXIT_DEPTH

                self.warn(
                    f"Exit depth required {exit_depth_required}mm",
                    f"is greater than the depth allowed {MAX_DEPTH_INTO_BACKBOARD}mm"
                    "Switching to routing"
                )

                retval = None

            # Must be routed - use the contour bit if ok
            if not retval:
                if diameter > max(DRILLBIT_SIZES):
                    if diameter <= CONTOUR_ROUTER_DIAMETER_MM:
                        self.add( 1j * CONTOUR_ROUTER_DIAMETER_MM )
                    else:
                        logger.error(
                            f"No suitable tool to route oblong holes of diameter "
                            "{TO_MM(diameter)}mm"
                        )
                else:
                    logger.error(
                        f"No suitable tool found to route oblong holes of diameter "
                        "{TO_MM(diameter)}mm"
                    )
            else:
                self.add(retval)

        return retval

    def merge(self, rack: Self):
        """
        Merge all the tools from the given rack into this one
        """
        def merge_set(tools):
            for dia in tools:
                if dia not in self.keys():
                    pos = self.find_free_position(False)

                    if pos is None:
                        # Look for unused bits in the rack and replace them
                        replaced = False

                        for dia, slot in self.items():
                            if dia not in rack:
                                # Remove!
                                self.add_bit(dia, slot)
                                replaced = True
                                break

                        if not replaced:
                            logger.error(f"Rack is full. Cannot add tool {DIA_TO_STR(dia)}")
                    else:
                        self.add_bit(dia, pos)

        # Iterate drill bits first
        merge_set( [tool for tool in self.key() if not tool.imag] )
        merge_set( [tool for tool in self.key() if tool.imag] )

    def diff(self, rack:Self):
        """
        Diff racks and compile a list of actions from the operator
        This rack is the final rack
        """
        retval = OrderedDict() # type: Dict[int, tuple[str, complex]]

        for slot in self.values():
            this_dia = self.rack[slot]
            their_dia = rack.get_tool(slot)

            if this_dia is None:
                continue

            if their_dia is None:
                retval[slot] = ("ADD", this_dia)
            else:
                retval[slot] = ("REPLACE", this_dia)

        return retval

    def remove_bit(self, bit):
        self.rack.remove(bit)

    def find_free_position(self, extend=True):
        """
        Return a tool position position in the rack which is free.
        By default, it will return the last position from the end which
        is free, otherwise, the next position from the end
        Rationale: If a space is left at the start - it usually serves a
        specific function.
        Note: Tool position starts from 1.

        x x x i x i x x
        """
        retval = None

        for i in range(len(self.rack), 0, -1):
            zi = i - 1
            if self.rack[zi] is None:
                retval = i
                continue

            if retval is None:
                if extend:
                    self.rack.append(None)
                    retval = len(self.rack)
                    break
                elif zi == 0:
                    # No more
                    return None

        return retval

    def __repr__(self):
        rack_str = ""
        for (id, dia) in enumerate(self.rack):
            if dia is None:
                rack_str += f"T{id+1:02}:x "
            elif dia.imag:
                rack_str += f"T{id+1:02}:R{dia.imag} "
            else:
                rack_str += f"T{id+1:02}:{dia} "
        return rack_str


class RackManager:
    """
    Object which manages the racks of the CNC.
    If the CNC has automated tool change, this is very important to
    allow the operator from reusing existing racks and speed operations.
    Depending on the CNC, the racks could be loadable, so each Job could
    have its own rack.
    A file (path defined in the settings) is used to create the rack
    configuration.
    The machining code can also create a new rack from scratch, and it
    can be saved.
    Finally for the less fortunate, the rack 'manual', is used to manually
    change the tools, and is considered of size unlimited.
    """
    def __init__(self) -> None:
        # Contains the parse Yaml
        rack_data = {}

        # Load the YAML schema
        try:
            with open(RACK_SCHEMA_FILE) as schema_file:
                schema = yaml.safe_load(schema_file)
                compiled_schema = jsonschema.Draft7Validator(schema)
        except OSError:
            logger.error(f"The schema file {RACK_SCHEMA_FILE.absolute()} could not be opened!")
        except yaml.YAMLError:
            logger.error(f"The schema file {RACK_SCHEMA_FILE.absolute()} is not a valid Yaml document!")
            logger.error(e)
        except jsonschema.ValidationError:
            logger.error(f"The schema file {RACK_SCHEMA_FILE.absolute()} is invalid!")
        else:
            # Load the rack file
            if RACK_FILE.exists():
                try:
                    with open(RACK_FILE) as rack_yaml:
                        rack_data = yaml.safe_load(rack_yaml)

                    # Perform the validation using the compiled schema
                    errors = list(compiled_schema.iter_errors(rack_data))

                    if errors:
                        rack_data = None
                        for error in errors:
                            logger.error("Rack validation error:" + error.message)
                except OSError:
                    logger.error(f"Failed to open {RACK_FILE.absolute()}. No rack loaded.")
                except yaml.YAMLError as e:
                    logger.error(f"The rack file {RACK_FILE.absolute()} is not a valid Yaml document")
                    logger.error(e)
                else:
                    logger.debug(rack_data)
            else:
                # If we don't have a rack - create one!
                if rack_data is None:
                    logger.info("No suitable rack file found. Creating a new rack file.")

                    from datetime import datetime
                    formatted_date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Load the template file
                    try:
                        template_content = TEMPLATE_RACK_FILE.read_text()
                        RACK_FILE.write_text(template_content.format(datetime=formatted_date_time, schema_file=RACK_SCHEMA_FILE))
                    except:
                        logger.error(f"Failed to create {RACK_FILE.absolute}. Check permissions")

        # Process the rack_data
        self.issue = rack_data.get("issue", 0)
        self.size = rack_data.get("size", 0)
        self.rack = Rack(self.size)

        selection = rack_data.get("use")
        racks_definition = rack_data.get("racks", {})

        try:
            if selection:
                if selection not in racks_definition:
                    raise Exception(f"Cannot find the rack named '{selection}' in the 'use' statement.")

                if self.size == 0:
                    raise Exception(f"You must specify the size of the racks other than 0.")

                for tool_definition in racks_definition[selection]:
                    number = tool_definition.get("number", None)

                    bit_dia = tool_definition.get("drill", tool_definition.get("router"))

                    # Magic values to avoid stupid value done simply
                    if CHECK_WITHIN_DIAMETERS_ABSOLUTE_RANGE(bit_dia):
                        # Check the diameter matches with the declared drill sizes
                        if "router" in tool_definition:
                            if bit_dia not in ROUTERBIT_SIZES:
                                logger.warn(f"T{number} in the rack '{selection}' has a non standard diameter {bit_dia}.")

                            # Make into imaginary number to indicate it is a router
                            bit_dia *= 1j
                        elif bit_dia not in DRILLBIT_SIZES:
                            logger.warn(f"T{number} in the rack '{selection}' has a non standard diameter {bit_dia}.")

                        # The rack will fill the slot by increment if number is None
                        self.rack.add_bit(bit_dia, number)
                    else:
                        raise Exception(f"Bit size {bit_dia} is not supported")

        except Exception as e:
            logger.error(e)
            # Reset the rack to manuak
            logger.warning("Back rack configuration detected. Using manual rack.")
            self.rack = Rack()

    def save(self, RACK_FILE):
        pass

    def get_rack(self):
        """ @return A deep copy of the current rack """
        return self.rack.clone(False)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    r = RackManager()
    print(r.rack)
