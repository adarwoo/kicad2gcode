#!/usr/bin/python3
from config import config
from units import Quantity


# Defines the StockRoom class.
# This class defines a virtual stock room storing Consumables
# (stock with normal wear and tear) and fixtures.

# The stockroom is persisted in a Yaml file.
# The idea, is that the Yaml could be edited - but also persisted.

class StockItem:
    """
    The base class for all items stored in the stock room
    """
    def __init__(self, name, **kwargs):
        self.name=name
        self.conf=kwargs

# Types only
class Consumable(StockItem):
    pass

class Fixture(StockItem):
    pass
