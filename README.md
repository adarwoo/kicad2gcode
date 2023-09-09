# pcb2gcode

This project aims at providing a highly customisable tool to generate some GCode
for any CNC directly from a KiCAD PCB file.
It aims to be used in 3 different ways:
1. As a KiCAD plugin, so the GCode can be produced right from KiCAD
2. As a standalone command line type application for automation into other processed
3. As an API to use in a more integrated solution such as a Rasperry Pi connected to the CNC

**NOTE**: THIS IS WORK IN PROGRESS. It is activelly being developped but is not completed.

## Features

### Support for ATC and manual tool change
Define standard racks and use them.
The existing rack is evaluated and an updated version is generated along with
instructions for the changes required (add or replace a bit).

Racks are optimized to minimise the number of tool changes and are always sorted
to make the operator's life easier.
Racks can have un-usable slots too.

Get rack composition clearly layed out for you.

### Custom shop tools
Define you cutting tools on hand and let the software work it out for you.
It uses your tolerance to optimise the work.
If holes cannot be drilled (no adequate size), a router bit is used instead.
The software check the drilling depth required based on the bit diameter and
geometry and ensure it does not go through the backing board.

### Optimized machining
A Travelling Salesman Problem is applied throughout to minimise traveling time.
This is applied for drilling and routing.

### Support for different units
Versed in all unit systems, you can use the unit you prefer. This can be
used throughout the configuration. The units used are kept throughout.
Imperial can also be expressed in fractions, with the fractions kept in the display.

### Manufacturer's data
The configuration comes with manufacturing data to optimize the experience for
each cutting tool.
The software can extrapolate the manufacturing data for in-between sizes.
The generated code optimised the feed rate and spindle speed based on the
manufacturing data and the CNC capability.

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
