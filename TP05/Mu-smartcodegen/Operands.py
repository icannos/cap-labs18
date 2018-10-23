from MuParser import MuParser

"""
MIF08, CAP, CodeGeneration, TARGET18 API
 Classes for data location: temporarys, registers, memory
"""


class AllocationError(Exception):
    """
    Useful to properly launch an error!
    """

    def __init__(self, msg):
        super().__init__(msg)


class Operand():
    pass


# 2018 signed version.
# attention il reste des bugs dans le simulateur pour sge/slt
all_ops = ['slt', 'sgt', 'eq', 'neq', 'sle', 'sge']
opdict = dict([(MuParser.LT, 'slt'), (MuParser.GT, 'sgt'),
               (MuParser.LTEQ, 'sle'), (MuParser.GTEQ, 'sge'),
               (MuParser.NEQ, 'neq'), (MuParser.EQ, 'eq')])
opnot_dict = dict([('sgt', 'sle'), ('sge', 'slt'), ('slt', 'sge'),
                   ('sle', 'sgt'), ('eq', 'neq'), ('neq', 'eq')])


class Condition(Operand):
    """Condition, i.e. second operand of the Jumpif instruction. TODO regarder"""

    def __init__(self, optype):
        if optype in opdict:
            self._op = opdict[optype]
        elif str(optype) in all_ops:
            self._op = str(optype)
        else:
            raise Exception("Unsupported comparison operator %s", optype)

    def negate(self):
        return Condition(opnot_dict[self._op])

    def __str__(self):
        return self._op


class DataLocation(Operand):
    """ A Data Location is either a register, a temporary
    or a place in memory (offset)
    """

    def is_temporary(self):
        """True if the location is a temporary, i.e. needs to be replaced
        during code generation.
        """
        return False


class Offset(DataLocation):
    """ Offset = address in memory computed with base + offset
    """

    def __init__(self, basereg, offset):
        super().__init__()
        assert isinstance(offset, int)
        self._offset = offset
        self._basereg = basereg

    def __str__(self):
        return("offset {} from {}".format(self._offset, self._basereg))

    __repr__ = __str__

    def get_offset(self):
        return self._offset


class Register(DataLocation):
    """ A (physical) register
    """

    def __init__(self, number):
        super().__init__()
        self._number = number

    def __str__(self):
        return ("r{}".format(self._number))

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return isinstance(other, Register) and self._number == other._number

    def __hash__(self):
        return self._number


class RegisterAdd(DataLocation):
    """ A (physical) special register for addresses
    """

    def __init__(self, number):
        super().__init__()
        self._number = number

    def __str__(self):
        if self._number == 2:
            return "sp"
        else:
            return ("a{}".format(self._number))


class Indirect(DataLocation):
    """Operand of the form [reg], designating the memory location pointed
    to by reg."""

    def __init__(self, reg):
        super().__init__()
        self._reg = reg

    def __str__(self):
        return ("{}".format(self._reg))  # no []


class Immediate(DataLocation):
    """Immediate operand (integer)."""

    def __init__(self, val):
        super().__init__()
        self._val = val

    def __str__(self):
        return str(self._val)


class Char(DataLocation):
    """Immediate character operand (for print)."""

    def __init__(self, val):
        super().__init__()
        self._val = val

    def __str__(self):
        return str(self._val)


# Shortcuts for registers
R0 = Register(0)
R1 = Register(1)
R2 = Register(2)
R3 = Register(3)
R4 = Register(4)
R5 = Register(5)
R6 = Register(6)
R7 = Register(7)
A0 = RegisterAdd(0)
A1 = RegisterAdd(1)
SP = RegisterAdd(2)
# General purpose registers, usable for the allocator
GP_REGS = tuple(Register(i) for i in range(2, 8))


class TemporaryPool:
    """Manage a pool of temporarys."""

    def __init__(self):
        self._all_temps = set()
        self._allocation = None
        self._current_num = 0

    def add_tmp(self, reg):
        """Add a register to the pool."""
        self._all_temps.add(reg)

    def set_reg_allocation(self, allocation):
        """Give a mapping from temporarys to actual registers.
        allocation must be a dict from Temporary to Register.
        """
        self._allocation = allocation

    def new_tmp(self):
        """Give a new fresh temporary (temp)"""
        r = Temporary(self._current_num, self)
        self.add_tmp(r)
        self._current_num += 1
        return r

    def get_alloced_loc(self, reg):
        """Get the actual register allocated for the temporary reg."""
        return self._allocation[reg]


class Temporary(DataLocation):
    """Temporary, are locations that haven't been
    allocated yet. They will later be mapped to physical registers
    (Register) or to a memory location."""

    def __init__(self, number, pool):
        self._number = number
        self._pool = pool
        pool.add_tmp(self)

    def __str__(self):
        return("temp_{}".format(str(self._number)))

    __repr__ = __str__

    def get_alloced_loc(self):
        return self._pool.get_alloced_loc(self)

    def is_temporary(self):
        return True
