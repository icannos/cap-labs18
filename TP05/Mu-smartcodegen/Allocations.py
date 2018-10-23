from Operands import Temporary, A0, SP, R0, R1, Indirect, Register
from Instruction3A import (Instru3A)

"""
MIF08, CAP, 2018
Allocation "replace" functions for direct code generation.
Each function suppose that its corresponding alloc has been called before.
"""


def replace_reg(old_i):
    """Replace Temporary operands with
    the corresponding allocated register."""
    ins, old_args = old_i.unfold()
    args = []
    for arg in old_args:
        if isinstance(arg, Temporary):
            arg = arg.get_alloced_loc()
        args.append(arg)
    return [Instru3A(ins, args=args)]


def replace_mem(old_i):
    """Replace Temporary operands with the corresponding allocated
    memory location. SP points to the stack"""
    before = []
    after = []
    ins, old_args = old_i.unfold()
    args = []
    # TODO: compute before,after,args.
    i = Instru3A(ins, args=args)
    return before + [i] + after


def replace_smart(old_i):
    """Replace Temporary operands with the corresponding allocated
    physical register OR memory location. R6 points to the stack"""
    before = []
    after = []
    ins, old_args = old_i.unfold()
    args = []
    # TODO: compute before,after,args. This is a superset of what replace_mem does.
    # and now return the new list!
    i = Instru3A(ins, args=args)  # change argument list into args
    return before + [i] + after
