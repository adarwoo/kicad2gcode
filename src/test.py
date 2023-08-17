from pathlib import Path

import json
import jsonschema
from ruamel.yaml import YAML


# Yaml loaders and dumpers
from ruamel.yaml.main import \
    round_trip_load as yaml_load, \
    round_trip_dump as yaml_dump

# Yaml commentary
from ruamel.yaml.comments import \
    CommentedMap as OrderedDict, \
    CommentedSeq as OrderedList

# For manual creation of tokens
from ruamel.yaml.tokens import CommentToken
from ruamel.yaml.error import CommentMark

import logging

logger = logging.getLogger(__name__)


def generate_yaml_from_schema(schema_filename, output_filename):
    # Load the YAML schema
    schema = None
    try:
        with open(schema_filename) as schema_file:
            schema = json.load(schema_file)
            validator = jsonschema.Draft7Validator(schema)
    except OSError:
        logger.error(f"The schema file {schema_filename.absolute()} could not be opened!")
    except YAML.YAMLError as e:
        logger.error(f"The schema file {schema_filename.absolute()} is not a valid Yaml document!")
        logger.error(e)
    except jsonschema.ValidationError:
        logger.error(f"The schema file {schema_filename.absolute()} is invalid!")
    except Exception as e:
        print(e)
    else:
        # Validate schema using jsonschema
        errors = list(validator.iter_errors(schema))
        if errors:
            for error in errors:
                print("Validation Error:", error.message, error)
            return

    # Create YAML object
    yaml = YAML()
    yaml.indent(offset=2)

    # Create an empty dictionary for the generated YAML content
    yaml_content = {}
    yaml_content = yaml_load(
        yaml_dump(yaml_content),
        preserve_quotes=True
    )

    yaml_content.yaml_set_start_comment("Shopping Lists for date: "
                                     "23 Oct 2021")

    # Generate YAML content from the schema
    for property_name, property_info in schema['properties'].items():
        default_value = property_info.get('default')
        description = property_info.get('description', 'No description available')


        # Create a nested dictionary with comment and value
        yaml_content[property_name] = default_value
        yaml_content.get(property_name).yaml_add_eol_comment(description)

        # Add the property with default value
        yaml_content[property_name] = default_value

    # Write generated YAML content to file
    with open(output_filename, 'w') as output_file:
        yaml.dump(yaml_content, output_file)

if __name__ == '__main__':
    schema_filename = Path('input_schema.json')  # Update with your JSON schema file
    output_filename = 'output_file.yaml'   # Update with desired output YAML file

    generate_yaml_from_schema(schema_filename, output_filename)
    print("YAML file generated successfully!")
