# pcb2gcode

This project aims at providing a highly customisable tool to generate some GCode
for any CNC directly from a KiCAD PCB file.
It aims to be used in 3 different ways:
1. As a KiCAD plugin, so the GCode can be produced right from KiCAD
2. As a standalone command line type application for automation into other processed
3. As an API to use in a more integrated solution such as a Rasperry Pi connected to the CNC

**NOTE**: THIS IS WORK IN PROGRESS. It is activelly being developped but is not completed.

## Installation

The intent is to host it on pip -that's outstanding too.
```bash
$ pip install pcb2gcode
```

## Usage

```
Usage: pcb2gcode [OPTIONS] FILENAME

  A utility which take a KiCAD v7 PCB and creates the GCode for a CNC to drill
  and route the PCB. The utility is heavily configurable. The initial set of
  configuration files is create the first time the utility runs. You can then
  edit them. The default path is ~/.pcb2gcode.

Options:
  -p, --pth              Drill and route all requiring plating.
  -n, --npth             Final drills and route and non-plated features
  -l, --outline          Route the PCB outiline
  -a, --all              Do all operations
  -o, --output FILENAME  Specify an output file name. Defaults to stdout
  --help                 Show this message and exit.
```

## Contributing

My objective is to get a working application by Sept 2023. This should machine
holes and outlines (pth and npth).
The architecture has been thought also allow for engraving. But I have no need
for engraving for now as I etch PCBs.
Let me know if you are interrested in contributing.
The tests do not provide 100% coverage yet and the code could be cleaned up too.

## License

`pcb2gcode` was created by Guillaume ARRECKX.
It is licensed under the terms of the GNU General Public License v3.0 license.

## Credits

`pcb2gcode` was created with [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/) and the `py-pkgs-cookiecutter` [template](https://github.com/py-pkgs/py-pkgs-cookiecutter).
