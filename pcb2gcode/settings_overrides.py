#
# Constants used for the CNC
# Override all constants define in defaults

# Max speed of my Spindle is 60k - but at 52k the vibrations yield better result
MAX_SPINDLE_SPEED = 52000

# My drill bit sizes
DRILLBIT_SIZES = [
    0.35, 0.4, .45, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9,
    1.0, 1,1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.8, 1.9,
    2.0, 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9,
    3.0, 3.1, 3.175 ]

# My router bit size
ROUTERBIT_SIZES = [
    0.8, 1.0, 1.2, 1.4, 1.6, 1.8 ]
