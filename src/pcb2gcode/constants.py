# Default location to look for yaml configuration files
CONFIG_USER_PATH = "~/.pcb2gcode"

# Suffix added to schema files
SCHEMA_FILE__FILENAME_SUFFIX="_schema.yaml"

# Section names
CONFIG_SECTIONS = ["global_settings", "machining_data", "stock_items", "racks"]

# Check the bit size is within the industry range
CHECK_DIAMETER_WITHIN_ALLOWED_RANGE_MM = lambda d: 0.05 <= d <= 6.4
