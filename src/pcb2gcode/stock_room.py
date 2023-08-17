#!/usr/bin/python3

# Defines the StockRoom class.
# This class defines a virtual stock room storing Consumables
# (stock with normal wear and tear) and fixtures.

# The stockroom is persisted in a Yaml file.
# The idea, is that the Yaml could be edited - but also persisted.

class StockItem:
    """
    The base class for all items stored in the stock room
    """
    def __init__(self):
        pass


class Consumable(StockItem):
    def __init__(self):
        pass


class CuttingTool(Consumable):
    def __init__(self, diameter):
        self.diameter = diameter

class Fixture:
    pass


class StockRoom:
    pass

