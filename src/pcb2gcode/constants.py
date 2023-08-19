from pathlib import Path


# Path to this module
THIS_PATH = Path(__file__).parent

# Path to the schema files
SCHEMA_PATH = THIS_PATH / "schema"

# Default location to look for yaml configuration files
CONFIG_USER_PATH = "~/.pcb2gcode"

# Suffix added to schema files
SCHEMA_FILE__FILENAME_SUFFIX="_schema.yaml"

# Section names
CONFIG_SECTIONS = ["global_settings", "machining_data", "stock_items", "racks"]
