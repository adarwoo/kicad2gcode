#!/usr/bin/python3

from setuptools import setup, find_packages

setup(
    name='pcb2gcode',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'src/pcb2gcode': ['conf/*']
    },
    install_requires=[
        # List your dependencies here
    ],
    author='Guillaume ARRECKX',
    author_email='software@arreckx.com',
    description='A module for converting PCB designs to G-code.',
    url='https://github.com/yourusername/pcb2gcode',
)
