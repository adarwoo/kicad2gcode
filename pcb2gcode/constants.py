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
Containts all constants and magic numbers which are not configurable and
consititute immutable or default values.
"""

from pathlib import Path


# Path to this module
THIS_PATH = Path(__file__).parent

# Path to the schema files
SCHEMA_PATH = THIS_PATH / "schema"

# Default location to look for yaml configuration files
CONFIG_USER_PATH = "~/.pcb2gcode"

# Suffix added to schema files
SCHEMA_FILE__FILENAME_SUFFIX="_schema.yaml"

# Suffix to append to the content yaml being renamed following a parsing error
YAML_FILE_RENAME_SUFFIX=".yaml.old"

# Section names for the configuration.
# A matching schema file must exists as SCHEMA_PATH/<section_name>SCHEMA_FILE__FILENAME_SUFFIX
CONFIG_SECTIONS = ["global_settings", "machining_data", "stock", "rack"]
