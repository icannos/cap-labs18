#!/usr/bin/python3
# -*- coding: utf-8 -*-

import sys

from Operands import (Condition, Immediate, Char,
                      Offset,
                      TemporaryPool,
                      AllocationError, Register, SP, Indirect,
                      GP_REGS)
from Instruction3A import Instru3A, Comment, Label
from Allocations import replace_reg, replace_mem


"""
MIF08, CAP, CodeGeneration, TARGET18 API
 Classes for a TARGET18 program: constructors, allocation, dump.
"""


class TARGET18Prog:
    """Representation of a TARGET18 program (i.e. list of
    instructions)."""
    def __init__(self):
        self._listIns = []
        self._nbtmp = -1
        self._nblabel = -1
        self._dec = -1
        self._pool = TemporaryPool()
        # CFG Stuff - Lab 5 Only
        self._start = None
        self._end = None
        self._mapin = {}  # will be map block -> set of variables
        self._mapout = {}
        self._mapdef = {}  # block : defined = killed vars in the block
        self._igraph = None  # interference graph

    def add_edge(self, src, dest):
        dest._in.append(src)
        src._out.append(dest)

    def add_instruction(self, i, linkwithsucc=True):
        """Utility function to add an instruction in the program.
        in Lab 4, only add at the end of the instruction list (_listIns)
        in Lab 5, will be used to also add in the CFG structure.
        """
        if not self._listIns:  # empty list: empty prg
            i._isnotStart = False
            self._start = i
            self._end = i
        else:
            if self._end is not None:
                self._end._out.append(i)
                i._in.append(self._end)
            self._end = i
            if not linkwithsucc:
                self._end = None
        self._listIns.append(i)
        return i

    def iter_instructions(self, f):
        """Iterate over instructions.

        For each real instruction (not label or comment), call f,
        which must return either None or a list of instruction. If it
        returns None, nothing happens. If it returns a list, then the
        instruction is replaced by this list.

        """
        i = 0
        while i < len(self._listIns):
            old_i = self._listIns[i]
            if not old_i.is_instruction():
                i += 1
                continue
            new_i_list = f(old_i)
            if new_i_list is None:
                i += 1
                continue
            del self._listIns[i]
            self._listIns.insert(i, Comment(str(old_i)))
            i += 1
            for new_i in new_i_list:
                self._listIns.insert(i, new_i)
                i += 1
            self._listIns.insert(i, Comment("end " + str(old_i)))
            i += 1

    def get_instructions(self):
        return self._listIns

    def new_location(self, three_addr):
        if three_addr:
            return self.new_tmp()
        else:
            return self.new_offset()

    def new_tmp(self):
        """
        Return a new fresh temporary (temp)
        """
        return self._pool.new_tmp()

    def new_offset(self, base):
        """
        Return a new offset in the memory stack
        """
        self._dec = self._dec + 1
        return Offset(base, self._dec)

    def new_label(self, name):
        """
        Return a new label
        """
        self._nblabel = self._nblabel + 1
        return Label(name + "_" + str(self._nblabel))

    def new_label_while(self):
        self._nblabel = self._nblabel + 1
        return (Label("l_while_begin_" + str(self._nblabel)),
                Label("l_while_end_" + str(self._nblabel)))

    def new_label_cond(self):
        self._nblabel = self._nblabel + 1
        return (Label("l_cond_neg_" + str(self._nblabel)),
                Label("l_cond_end_" + str(self._nblabel)))

    def new_label_if(self):
        self._nblabel = self._nblabel + 1
        return (Label("l_if_false_" + str(self._nblabel)),
                Label("l_if_end_" + str(self._nblabel)))

    # each instruction has its own "add in list" version
    def addLabel(self, s):
        return self.add_instruction(s)

    def addComment(self, s):
        self.add_instruction(Comment(s))

    # print instruction  TODO attention ça ne marche que pour des INT
    def addInstructionPRINT(self, expr):
        self.add_instruction(Instru3A("print signed", expr))
        self.add_instruction(Instru3A("print char", Char("'\\n'")))

    # test and cond jumps.
    def addInstructionJUMP(self, label):
        assert isinstance(label, Label)
        i = Instru3A("jump", label)
        self.add_instruction(i, False)
        # add in list but do not link with the following node
        self.add_edge(i, label)
        return i

    # TODO : regarder ce qu'on fait avec le JUMPI

    # Useful meta instruction for conditional jump
    def addInstructionCondJUMP(self, label, op1, c, op2):
        assert isinstance(label, Label)
        assert isinstance(c, Condition)
        i = Instru3A("cond_jump", args=[label, op1, c, op2])
        self.add_instruction(i)
        self.add_edge(i, label)  # useful in next lab
        return i

    # Arithmetic instructions #TODO complete
    def addInstructionADD(self, dr, sr1, sr2orimm7):  # add avec 2 ops.
        if isinstance(sr2orimm7, Immediate):
            self.add_instruction(
                Instru3A("add3i", dr, sr1, sr2orimm7))
        else:
            self.add_instruction(
                Instru3A("add3", dr, sr1, sr2orimm7))

    def addInstructionSUB(self, dr, sr1, sr2orimm7):
        if isinstance(sr2orimm7, Immediate):
            self.add_instruction(
                Instru3A("sub3i", dr, sr1, sr2orimm7))
        else:
            self.add_instruction(
                Instru3A("sub3", dr, sr1, sr2orimm7))

    def addInstructionAND(self, dr, sr1, sr2orimm7):
        self.add_instruction(
            Instru3A("and3", dr, sr1, sr2orimm7))

    def addInstructionOR(self, dr, sr1, sr2orimm7):
        self.add_instruction(
            Instru3A("or3", dr, sr1, sr2orimm7))

    def addInstructionXOR(self, dr, sr1, sr2orimm7):  # TODO verifier si il existe
        self.add_instruction(
            Instru3A("xor3", dr, sr1, sr2orimm7))

    # Copy values (immediate or in register)
    def addInstructionLETI(self, dr, imm7):
        self.add_instruction(Instru3A("leti", dr, imm7))

    def addInstructionLET(self, dr, sr):
        self.add_instruction(Instru3A("let", dr, sr))

    # Memory instructions - Meta Instructions

    def addInstructionRMEM(self, dr, sr):
        if isinstance(sr, Register):
            # Accept plain register where we expect an indirect
            # addressing mode.
            sr = Indirect(sr)
        self.add_instruction(Instru3A("rmem", dr, sr))

    def addInstructionWMEM(self, dr, sr):
        if isinstance(sr, Register):
            # Accept plain register where we expect an indirect
            # addressing mode.
            sr = Indirect(sr)
        self.add_instruction(Instru3A("wmem", dr, sr))

    # Allocation functions
    def naive_alloc(self):
        """ Allocate all temporaries to registers.
        Fail if there are too many temporaries."""
        regs = list(GP_REGS)  # Get a writable copy
        reg_allocation = dict()
        for tmp in self._pool._all_temps:
            try:
                reg = regs.pop()
            except IndexError:
                raise AllocationError(
                    "Too many temporaries ({}) for the naive allocation, sorry"
                    .format(len(self._pool._all_temps)))
            reg_allocation[tmp] = reg
        self._pool.set_reg_allocation(reg_allocation)
        self.iter_instructions(replace_reg)

    def alloc_to_mem(self):
        """Allocate all temporaries to memory. Hypothesis:
        - Expanded instructions can use r0 (to compute addresses), r1 and
        r2 (to store the values of temporaries before the actual
        instruction).
        """
        self._pool.set_reg_allocation(
            {vreg: self.new_offset(SP) for vreg in self._pool._all_temps})
        self.iter_instructions(replace_mem)

    # Dump code
    def printCode(self, filename, comment=None):
        # dump generated code on stdout or file.
        output = open(filename, 'w') if filename else sys.stdout
        output.write(
            ";;Automatically generated TARGET code, MIF08 & CAP 2018\n")
        if comment is not None:
            output.write(";;{} version\n".format(comment))
        # Stack in TARGET18 is managed with SP
        for i in self._listIns:
            i.printIns(output)
        output.write("\n\n;;postlude\n")
        output.write("end:\n	jump end\n")
        if output is not sys.stdout:
            output.close()

