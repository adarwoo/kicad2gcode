#!/usr/bin/env python3

#
# If a file does not exist, create it and load it.
# The default path
#
import jsonschema
import logging
import sys

from .constants import CONFIG_USER_PATH, CONFIG_SECTIONS, \
    SCHEMA_FILE__FILENAME_SUFFIX, SCHEMA_PATH

from pathlib import Path

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap, CommentedSeq

from .units import Unit

import re

from .bunch import bunchify

logger = logging.getLogger(__name__)

# Define a regex pattern
RE_SPLIT_UNIT = re.compile(r'(?P<unit>\w+)(\((?P<defaults_to>\w+)\))?')


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
    def _populate_defaults(schema):
        retval = None

        if 'default' in schema:
            retval = schema['default']
        elif 'const' in schema:
            retval = schema['const']
        elif 'type' in schema and schema['type'] == 'object':
            default_obj = CommentedMap()

            for prop_name, prop_schema in schema.get('properties', {}).items():
                default_value = __class__._populate_defaults(prop_schema)
                default_obj[prop_name] = default_value

            retval = default_obj
        elif 'type' in schema and schema['type'] == 'array':
            default_array = CommentedSeq()

            if 'items' in schema:
                default_item = __class__._populate_defaults(schema['items'])
                default_array.append(default_item)

            retval = default_array

        return retval

    @staticmethod
    def _add_comments(node, schema, indent=0):
        """
        Given the fully formed node, add comments using the schema description
        """
        if 'description' in schema:
            node.yaml_set_start_comment(schema['description'], indent)

        if 'type' in schema and schema['type'] == 'object':
            for prop_name, prop_schema in schema.get('properties', {}).items():
                if 'description' in prop_schema:
                    desc = prop_schema['description']
                    if indent==0:
                        desc = "\n" + desc

                    node.yaml_set_comment_before_after_key(prop_name, desc, indent)

                if prop_name in node:
                    if (
                        isinstance(node[prop_name], CommentedMap) or
                        isinstance(node[prop_name], CommentedSeq)
                    ):
                        __class__._add_comments(node[prop_name], prop_schema, indent+2)

        if 'type' in schema and schema['type'] == 'array':
            if 'items' in schema:
                __class__._add_comments(node[0], schema['items'], indent+2)


    @staticmethod
    def convert_values_to_units(node, schema):
        """
        Look for scalar values with a unit, and override the scalar using a Quantity
        If the unit has as '/x', make x the default unit
        """
        if 'type' in schema and schema['type'] == 'object':
            for prop_name, prop_schema in schema.get('properties', {}).items():
                if prop_name in node:
                    if (
                        isinstance(node[prop_name], CommentedMap) or
                        isinstance(node[prop_name], CommentedSeq)
                    ):
                        __class__.convert_values_to_units(node[prop_name], prop_schema)
                    else: # Scalar
                        if 'unit' in prop_schema:
                            match = RE_SPLIT_UNIT.match(prop_schema['unit'])
                            assert(match)
                            unit_cls = Unit.get_type(match.group("unit"))
                            defaults_to = match.group("defaults_to") or ""
                            # Override the value using a Quantity
                            node[prop_name] = unit_cls.from_string(
                                str(node[prop_name]), defaults_to)

        if 'type' in schema and schema['type'] == 'array':
            if 'items' in schema:
                for i, single in enumerate(node):
                    if (
                        isinstance(single, CommentedMap) or
                        isinstance(single, CommentedSeq)
                    ):
                        __class__.convert_values_to_units(single, schema['items'])
                    else: # Scalar
                        if 'unit' in schema:
                            match = RE_SPLIT_UNIT.match(schema['unit'])
                            assert(match)
                            unit_cls = Unit.get_type(match.group("unit"))
                            defaults_to = match.group("defaults_to") or ""
                            # Override the value using a Quantity
                            node[i] = unit_cls.from_string(
                                str(single), defaults_to)

    def load_schema(self):
        import sys
        from importlib import resources

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
                retval = self.yaml.load(stream)
                jsonschema.validate(retval, self.schema)

            return retval
        except OSError:
            logger.error("File '%s' could not be opened!", self.config_file_path)
        except ruamel.yaml.YAMLError as exception:
            logger.error("File '%s' is not a valid Yaml document!", self.config_file_path)
            logger.error(exception)
        except jsonschema.ValidationError as exc:
            logger.error("File '%s' is not structured correctly!", self.config_file_path)
            logger.info("Details:\n%s", exc)
        except Exception as exception:
            logger.error("Failed to interpret the content of '%s'", self.config_file_path)
            logger.error("Got: %s", exception)

        # Since we failed to include the file succesfully, rename this one to make room for a fresh one
        newname = self.config_file_path.with_suffix(".yaml.old")

        try:
            retval = {}
            logger.warning("Renaming the file %s", newname)
            self.config_file_path.replace(newname)
        except Exception as exception:
            logger.error("Failed to rename the file '%s' to '%s'", self.config_file_path, newname)
            logger.error("Got: %s", exception)

        return retval

    def generate_default_content(self):
        # Generate a default content
        default_config = self._populate_defaults(self.schema)
        self._add_comments(default_config, self.schema)

        return default_config

    def write_content(self):
        # Overwrite the file
        # Make sure the directory exists
        config_dir = self.config_file_path.parent

        logger.info("Creating a default content %s", self.config_file_path)

        if not config_dir.exists():
            try:
                logger.info("Creating the directory %s", config_dir)
                config_dir.mkdir(0o0755, True, True)
            except Exception as exception:
                logger.error("Failed to create the directory '%s'", config_dir)
                logger.error("Got: %s", exception)

                # File won't be created
                return

        try:
            with open(self.config_file_path, 'w') as content_file:
                self.yaml.dump(self.content, content_file)
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
        from ruamel.yaml import YAML

        self.section_name = section_name
        self.config_file_path = Path(
            expanduser(CONFIG_USER_PATH) / Path(section_name + ".yaml")
        )

        self.yaml = YAML()
        self.schema, self.validator = self.load_schema()
        self.content = self.load_content()

        if self.content == {}:
            self.content = self.generate_default_content()
            self.write_content()

        self.convert_values_to_units(self.content, self.schema)

    def get_content(self):
        return self.content

# Create new dictionary dynamically in this module
for section in CONFIG_SECTIONS:
    yaml_config = YamlConfigManager(section)

    # Add to the config object as a flat structure
    bunch = bunchify(yaml_config.get_content())
    setattr(sys.modules[__name__], section, bunch)
