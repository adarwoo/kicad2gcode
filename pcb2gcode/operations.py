from enum import IntEnum


class Operations(IntEnum):
    """ Used to tell the Machining class which holes to do """
    NONE = 0
    PTH = 0b0001        # Includes routing oblongs
    NPTH = 0b0010       # Includes routing oblongs
    OUTLINE = 0b0100    # Only routing of the outline
    
    FIRST = PTH
    FINAL = NPTH | OUTLINE
    ALL = FIRST | FINAL
        