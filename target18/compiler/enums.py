#!/usr/bin/env python3
import enum
import collections
import math

Token = collections.namedtuple('Token', ['typ', 'value', 'filename', 'line', 'column'])
Value = collections.namedtuple("Value", ("typ", "raw_value"))
Line = collections.namedtuple("Line", ("funcname", "typed_args", "linenumber", "filename"))

NB_REG = 8
NB_BIT_REG = 3


class AutoNumber(enum.Enum):
    def __new__(cls):
        value = len(cls.__members__) + 1
        obj = object.__new__(cls)
        obj._value_ = value
        return obj


class LexType(AutoNumber):
    """ Type enum for lexer's token """
    MEMCOUNTER = ()
    OPERATION = ()
    DIRECTION = ()
    FORMAT = ()
    CONDITION = ()
    REGISTER = ()
    COMMENT = ()
    NEWLINE = ()
    ENDFILE = ()
    INCLUDE = ()
    LITSTRING = ()
    STRING = ()
    NUMBER = ()
    LABEL = ()
    SKIP = ()
    BINARY = ()
    CONS = ()
    CHAR = ()
    MISMATCH = ()


class ValueType(AutoNumber):
    MEMCOUNTER = ()
    DIRECTION = ()
    CONDITION = ()
    FORMAT = ()
    STRING = ()
    UCONSTANT = ()  # Unsigned Constant
    SCONSTANT = ()  # Signed Constant
    RADDRESS = ()  # Relative address
    AADDRESS = ()  # Absolute address
    SHIFTVAL = ()
    REGISTER = ()
    LABEL = ()
    SIZE = ()
    BINARY = ()
