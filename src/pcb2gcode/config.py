#
# If a file does not exist, create it and load it.
# The default path 
#
import logging

from constants import CONFIG_PATH
from pathlib import Path
    
import ruamel.yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq


logger = logging.getLogger(__name__)


class YamlConfigManager:
    """
    The manager does the following:
     - It opens a schema file (and checks it)
     - It tries to open a configuration file
     - If opens OK - tries to parse it then validate the content against the schema.
     -   If it validates - It returns the content as a Python object
     -   Else, 
            it renames the config file 
            Tries to generates a new default content based on the schema file
     -      it returns the default content
    """
    @staticmethod
    def _populate_defaults(node, schema):
        if 'default' in schema:
            return schema['default']
        if 'const' in schema:
            return schema['const']
        
        if 'type' in schema and schema['type'] == 'object':
            default_obj = CommentedMap()
            for prop_name, prop_schema in schema.get('properties', {}).items():
                default_value = __class__._populate_defaults({}, prop_schema)
                default_obj[prop_name] = default_value
            return default_obj
        
        if 'type' in schema and schema['type'] == 'array':
            default_array = CommentedSeq()
            if 'items' in schema:
                default_item = __class__._populate_defaults({}, schema['items'])
                default_array.append(default_item)
            return default_array
        
        return None

    @staticmethod
    def _add_comments(node, schema, owner=None, indent=0):
        """
        Write the default data to a YAML file with comments
        """
        if 'description' in schema:
            if node:
                node.yaml_set_start_comment(schema['description'], indent)

        if 'type' in schema and schema['type'] == 'object':
            for prop_name, prop_schema in schema.get('properties', {}).items():
                if prop_name in node:
                    __class__._add_comments(node[prop_name], prop_schema, node, indent+2)
        
        if 'type' in schema and schema['type'] == 'array':
            if 'items' in schema:
                __class__._add_comments(node[0], schema['items'], node, indent+2)

    def load_schema(self):
        from importlib import resources
        from constants import SCHEMA_FILE__FILENAME_SUFFIX

        self.schema_file_path = Path(
            self.section_name + SCHEMA_FILE__FILENAME_SUFFIX)
        
        if not self.schema_file_path.exists():
            logger.critical(f"Missing schema file: {self.schema_file_path}")
            raise RuntimeError("Corrupt package")
        
        try:
            with open(self.schema_file_path, 'r') as self.schema_file_path:
                schema = ruamel.yaml.YAML().load(self.schema_file_path)
        except Exception as e:
            logger.critical(f"Failed to process the schema file: {self.schema_file_path}")
            logger.error("Got:" + e)
            raise RuntimeError("Schema error")
        
        # The schema must be error free
        return schema
    
    def load_content(self):
        retval = {}

        if self.config_file_path.exists():
            # Parse it!
            try:
                retval = {} # TODO
            except Exception as e:
                # Bad parsing - rename
                logger.error(f"Failed to interpret the content of {self.config_file_path}")
                logger.error("Got: " + e)

                # Try renaming the bad file
                newname = self.config_file_path.with_suffix(".yaml.old")
                try:
                    self.config_file_path.replace(newname)
                    logger.error(f"Renaming the file {newname}")
                except Exception as e:
                    logger.error(f"Failed to rename the file {self.config_file_path} to {newname}")
                    logger.error("Got: " + e)

        return retval
    
    def generate_default_content(self):
        # Generate a default content
        default_config = self.populate_defaults({}, self.schema)
        self.add_comments(default_config, self.schema)

        return default_config

    def write_content(self):
        # Overwrite the file
        try:
            with open(self.config_file_path, 'w') as content_file:
                ruamel.yaml.dump(self.content, content_file, Dumper=ruamel.yaml.RoundTripDumper)
        except Exception as e:
            logger.error(f"Failed to create a default configuration file {self.config_file_path}")

    def __init__(self, section_name) -> dict:
        """
        TODO:
        @param section_name The name of section of configuration to handle such as 'rack'
        """
        from os.path import expanduser
        from constants import CONFIG_USER_PATH

        self.section_name = section_name
        self.config_file_path = Path(
            expanduser(CONFIG_USER_PATH) / section_name + ".yaml")

        self.schema = self.load_schema()
        self.content = self.load_content()

        if not self.content:
            self.content = self.generate_default_content()
            self.write_content()

    @property
    def content(self):
        return self.content


class Config:
    def __init__(self) -> None:
        from constants import CONFIG_SECTIONS

        for section in CONFIG_SECTIONS:
            yaml_config = YamlConfigManager(section)
            setattr(self, section, yaml_config.content)


# Create a unique config instance
config = Config()
