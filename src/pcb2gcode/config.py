#!/usr/bin/env python3

#
# If a file does not exist, create it and load it.
# The default path 
#
import jsonschema
import logging

from constants import CONFIG_USER_PATH
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
            if node and isinstance(node, CommentedMap):
                node.yaml_set_start_comment(schema['description'], indent)

        if 'type' in schema and schema['type'] == 'object':
            for prop_name, prop_schema in schema.get('properties', {}).items():
                if prop_name in node:
                    __class__._add_comments(node[prop_name], prop_schema, node, indent+2)

        if 'type' in schema and schema['type'] == 'array':
            if 'items' in schema:
                __class__._add_comments(node[0], schema['items'], node, indent+2)

    def load_schema(self):
        import sys
        from importlib import resources
        from constants import SCHEMA_FILE__FILENAME_SUFFIX, SCHEMA_PATH

        self.schema_file_path = SCHEMA_PATH / Path(self.section_name + SCHEMA_FILE__FILENAME_SUFFIX)

        if not self.schema_file_path.exists():
            logger.critical("Missing schema file: %s", self.schema_file_path)
            raise RuntimeError("Corrupt package")

        try:
            with open(self.schema_file_path, 'r', encoding="utf-8") as self.schema_file_path:
                schema = ruamel.yaml.YAML().load(self.schema_file_path)
                validator = jsonschema.Draft7Validator(schema)
        except Exception as exception:
            logger.critical("Failed to process the schema file: %s", self.schema_file_path)
            logger.error("Got: %s", exception)
            raise RuntimeError(exception) from exception

        # The schema must be error free
        return schema, validator

    def load_content(self):
        retval = {}

        try:
            if not self.config_file_path.exists():
                logger.info("Configuration file '%s' is missing and will be created.", self.config_file_path)
                return retval
        except PermissionError:
            logger.info("Configuration file '%s' cannot be accessed.", self.config_file_path)
            return retval

        # Parse it!
        try:
            with open(self.config_file_path) as stream:
                retval = ruamel.yaml.safe_load(stream)
                jsonschema.validate(instance=stream, schema=self.schema)
            
            return retval
        except OSError:
            logger.error("File '%s' could not be opened!", self.config_file_path)
        except ruamel.yaml.YAMLError as exception:
            logger.error("File '%s' is not a valid Yaml document!", self.config_file_path)
            logger.error(e)
        except jsonschema.ValidationError:
            logger.error("File '%s' is not structured correctly!", self.config_file_path)
        except Exception as exception:
            logger.error("Failed to interpret the content of '%s'", self.config_file_path)
            logger.error("Got: %s", exception)

        # Since we failed to include the file succesfully, rename this one to make room for a fresh one
        newname = self.config_file_path.with_suffix(".yaml.old")

        try:
            self.config_file_path.replace(newname)
            logger.warning("Renaming the file %s", newname)
        except Exception as exception:
            logger.error("Failed to rename the file '%s' to '%s'", self.config_file_path, newname)
            logger.error("Got: %s", exception)

        return retval

    def generate_default_content(self):
        # Generate a default content
        default_config = self._populate_defaults({}, self.schema)
        self._add_comments(default_config, self.schema)

        return default_config

    def write_content(self):
        # Overwrite the file
        # Make sure the directory exists
        config_dir = self.config_file_path.parent

        if not config_dir.exists():
            try:
                config_dir.mkdir(644, True, True)
            except Exception as exception:
                logger.error("Failed to create the directory '%s'", config_dir)
                logger.error("Got: %s", exception)

                # File won't be created
                return

        try:
            with open(self.config_file_path, 'w') as content_file:
                ruamel.yaml.dump(self.content, content_file, Dumper=ruamel.yaml.RoundTripDumper)
        except Exception as exception:
            logger.error("Failed to create a default configuration file '%s'", self.config_file_path)
            logger.error("Got: %s", exception)

    def __init__(self, section_name: str) -> dict:
        """
        Create an instance of a Yaml configuration manager
        This manager is reponsible for processing a given Yaml configuration file.
        Doing so, guarantees a content to the caller.
        If the configuration file exists, it is parsed and checked against a schema.
        On errors, the file is renamed, an error generated, and a new file is created using the
        default values.

        @param section_name The name of section of configuration to handle such as 'racks'
        """
        from os.path import expanduser
        from constants import CONFIG_USER_PATH

        self.section_name = section_name
        self.config_file_path = Path(
            expanduser(CONFIG_USER_PATH) / Path(section_name + ".yaml")
        )

        self.schema, self.validator = self.load_schema()
        self.content = self.load_content()

        if not self.content:
            self.content = self.generate_default_content()
            self.write_content()

    def get_content(self):
        return self.content


class Config:
    def __init__(self) -> None:
        from constants import CONFIG_SECTIONS

        for section in CONFIG_SECTIONS:
            yaml_config = YamlConfigManager(section)

            # Multiword sections should be abreviated. Global settings becomes gs
            if '_' in section:
                section = ''.join([word[0] for word in section.split('_')])

            # Add to the config object
            setattr(self, section, yaml_config.get_content())

if __name__ == "__main__":
    import logging
    import sys
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

# Create a unique config instance
config = Config()
