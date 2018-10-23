from MuVisitor import MuVisitor
from MuParser import MuParser
from APICode18 import (TARGET18Prog, Condition)
from Operands import R0
from antlr4.tree.Trees import Trees

"""
CAP, MIF08, three-address code generation + simple alloc
This visitor constructs an object of type "TARGET18Prog"
and the corresponding CFG
"""


class MuCodeGen3AVisitor(MuVisitor):

    def __init__(self, d, parser):
        super().__init__()
        self._parser = parser
        self._debug = d
        self._memory = dict()
        # 3-address code generation
        self._prog = TARGET18Prog()
        self._lastlabel = ""
        self.ctx_stack = []  # useful for nested ITE

    def get_prog(self):
        return self._prog

    def printRegisterMap(self):
        print("--variables to memory map--")
        for keys, values in self._memory.items():
            print(keys + '-->' + str(values))

    # handle variable decl

    def visitVarDecl(self, ctx):
        vars_l = self.visit(ctx.id_l())
        for name in vars_l:
            if name in self._memory:
                print("Warning, variable %s has already been declared", name)
            else:
                self._memory[name] = self._prog.new_tmp()
        return

    def visitIdList(self, ctx):
        t = self.visit(ctx.id_l())
        t.append(ctx.ID().getText())
        return t

    def visitIdListBase(self, ctx):
        return [ctx.ID().getText()]

    # expressions

    def visitParExpr(self, ctx):
        return self.visit(ctx.expr())

    def visitNumberAtom(self, ctx):
        s = ctx.getText()
        try:
            val = int(s)
            # this is valid for val beetween -2^15 and 2^15 -1
            dr = self._prog.new_tmp()
            self._prog.addInstructionLETI(dr, val)
            return dr
        except ValueError:
            raise Exception("Not Yet Implemented (float value)")

    def visitBooleanAtom(self, ctx):
        # true is 1 false is 0
        b = ctx.getText()
        dr = self._prog.new_tmp()
        if b == 'true':
            val = 1
        else:
            val = 0
        self._prog.addInstructionLETI(dr, val)
        return dr

    def visitIdAtom(self, ctx):
        try:
            # get the register or the shift(dec) associated to id
            regval = self._memory[ctx.getText()]
            return regval
        except KeyError:
            raise Exception("Undefined variable, this should have failed to typecheck.")

    def visitStringAtom(self, ctx):
        raise Exception("Not Yet Implemented (string atom)")

    def visitAtomExpr(self, ctx):
        return self.visit(ctx.atom())

    def visitAdditiveExpr(self, ctx):
        tmpl = self.visit(ctx.expr(0))
        tmpr = self.visit(ctx.expr(1))
        dr = self._prog.new_tmp()
        if ctx.myop.type == MuParser.PLUS:
            self._prog.addInstructionADD(dr, tmpl, tmpr)
        else:
            self._prog.addInstructionSUB(dr, tmpl, tmpr)
        return dr

    def visitOrExpr(self, ctx):
        tmpl = self.visit(ctx.expr(0))
        tmpr = self.visit(ctx.expr(1))
        dr = self._prog.new_tmp()
        self._prog.addInstructionOR(dr, tmpl, tmpr)
        return dr

    def visitAndExpr(self, ctx):
        tmpl = self.visit(ctx.expr(0))
        tmpr = self.visit(ctx.expr(1))
        dr = self._prog.new_tmp()
        self._prog.addInstructionAND(dr, tmpl, tmpr)
        return dr

    def visitEqualityExpr(self, ctx):
        return self.visitRelationalExpr(ctx)

    def visitRelationalExpr(self, ctx):
        if self._debug:
            print("relational expression:")
            print(Trees.toStringTree(ctx, None, self._parser))
        tmpl = self.visit(ctx.expr(0))
        tmpr = self.visit(ctx.expr(1))
        c = Condition(ctx.myop.type)
        dest = self._prog.new_tmp()
        end_relational = self._prog.new_label('end_relational')
        self._prog.addInstructionLETI(dest, 0)
        self._prog.addInstructionCondJUMP(end_relational, tmpl, c.negate(),
                                          tmpr)
        self._prog.addInstructionLETI(dest, 1)
        self._prog.addLabel(end_relational)
        return dest

    def visitMultiplicativeExpr(self, ctx):
        raise Exception("Not Yet Implemented (multexpr)")

    def visitNotExpr(self, ctx):
        reg = self.visit(ctx.expr())
        dr = self._prog.new_tmp()
        # there is no NOT instruction :-(
        labelneg, labelend = self._prog.newlabelCond()
        self._prog.addInstructionCondJUMP(labelneg, reg,
                                          Condition("neq"), 1)
        self._prog.addInstructionLETI(dr, 0)
        self._prog.addInstructionJUMP(labelend)
        self._prog.addLabel(labelneg)
        self._prog.addInstructionLETI(dr, 1)
        self._prog.addLabel(labelend)
        return dr

    def visitUnaryMinusExpr(self, ctx):
        raise Exception("Not Yet Implemented (unaryminusexpr)")

    def visitPowExpr(self, ctx):
        raise Exception("Not Yet Implemented (powexpr)")

# statements
    def visitProgRule(self, ctx):
        self.visit(ctx.vardecl_l())
        self.visit(ctx.block())
        if self._debug:
            self.printRegisterMap()

    def visitAssignStat(self, ctx):
        if self._debug:
            print("assign statement, rightexpression is:")
            print(Trees.toStringTree(ctx.expr(), None, self._parser))
        reg4expr = self.visit(ctx.expr())
        name = ctx.ID().getText()
        # find in table
        if name in self._memory:
            self._prog.addInstructionLET(self._memory[name], reg4expr)
        else:
            raise Exception("Variable is not declared")

    def visitCondBlock(self, ctx):
        if self._debug:
            print("condblockstatement, condition is:")
            print(Trees.toStringTree(ctx.expr(), None, self._parser))
            print("and block is:")
            print(Trees.toStringTree(ctx.stat_block(), None, self._parser))
        end_if = self.ctx_stack[-1]  # get the label for the end!
        next_cond = self._prog.new_label('end_cond')
        cond = self.visit(ctx.expr())
        self._prog.addInstructionCondJUMP(next_cond, cond,
                                          Condition("eq"), 0)
        self.visit(ctx.stat_block())
        self._prog.addInstructionJUMP(end_if)
        self._prog.addLabel(next_cond)

    def visitIfStat(self, ctx):
        if self._debug:
            print("if statement")
        # invent a new label, then push in the label stack
        if_ctx_end_if = self._prog.new_label("end_if")
        self.ctx_stack.append(if_ctx_end_if)
        for cb in ctx.condition_block():
            self.visit(cb)  # append to the preceeding cond block- false
        if ctx.stat_block() is not None:
            if self._debug:
                print("else  ")
            self.visit(ctx.stat_block())  # else branch code
        # NOP, to avoid jump with offset +1.
        self._prog.addInstructionSUB(R0, R0, 0)
        # At the end, put the label and pop!
        self._prog.addLabel(if_ctx_end_if)
        assert self.ctx_stack.pop() is if_ctx_end_if

    def visitWhileStat(self, ctx):
        if self._debug:
            print("while statement, condition is:")
            print(Trees.toStringTree(ctx.expr(), None, self._parser))
            print("and block is:")
            print(Trees.toStringTree(ctx.stat_block(), None, self._parser))
            print("je suis là")
        labelbegin, labelend = self._prog.new_label_while()
        self._prog.addLabel(labelbegin)
        reg = self.visit(ctx.expr())
        self._prog.addInstructionCondJUMP(labelend, reg,
                                          Condition("neq"), 1)
        self.visit(ctx.stat_block())
        self._prog.addInstructionJUMP(labelbegin)
        self._prog.addLabel(labelend)

    def visitLogStat(self, ctx):
        expr_loc = self.visit(ctx.expr())
        if self._debug:
            print("log statement, expression is:")
            print(Trees.toStringTree(ctx.expr(), None, self._parser))
        self._prog.addInstructionPRINT(expr_loc)

    def visitStatList(self, ctx):
        for stat in ctx.stat():
            self._prog.addComment(Trees.toStringTree(stat, None, self._parser))
            self.visit(stat)
