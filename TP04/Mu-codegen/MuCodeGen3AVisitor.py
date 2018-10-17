from MuVisitor import MuVisitor
from MuParser import MuParser
from APICode18 import (TARGET18Prog, Condition)
from antlr4.tree.Trees import Trees

"""
CAP, MIF08, three-address code generation + simple alloc
This visitor constructs an object of type "TARGET18Prog"
"""


class MuCodeGen3AVisitor(MuVisitor):

    def __init__(self, d, s, parser):
        super().__init__()
        self._outputname = s
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
            raise NotImplementedError("float value")

    def visitBooleanAtom(self, ctx):
        # true is 1 false is 0
        raise NotImplementedError()

    def visitIdAtom(self, ctx):
        try:
            # get the register or the shift(dec) associated to id
            regval = self._memory[ctx.getText()]
            return regval
        except KeyError:  # do something, and check that it's the right exception ! TODO
            pass

    def visitStringAtom(self, ctx):
        raise NotImplementedError("string atom")

    def visitNilAtom(self, ctx):  # todo: see if ok
        raise NotImplementedError("nil atom")

    # now visit expressions : TODO

    def visitAtomExpr(self, ctx):
        return self.visit(ctx.atom())

    def visitAdditiveExpr(self, ctx):
        raise NotImplementedError()

    def visitOrExpr(self, ctx):
        raise NotImplementedError()

    def visitAndExpr(self, ctx):
        raise NotImplementedError()

    def visitEqualityExpr(self, ctx):
        return self.visitRelationalExpr(ctx)

    def visitRelationalExpr(self, ctx):
        if self._debug:
            print("relational expression:")
            print(Trees.toStringTree(ctx, None, self._parser))
        tmpl = self.visit(ctx.expr(0))
        tmpr = self.visit(ctx.expr(1))
        c = Condition(ctx.myop.type)
        raise NotImplementedError()

    def visitMultiplicativeExpr(self, ctx):
        raise NotImplementedError("multexpr")

    def visitNotExpr(self, ctx):
        reg = self.visit(ctx.expr())
        raise NotImplementedError()

    def visitUnaryMinusExpr(self, ctx):
        raise NotImplementedError("unaryminusexpr")

    def visitPowExpr(self, ctx):
        raise NotImplementedError("powexpr")

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
        raise NotImplementedError()

    def visitIfStat(self, ctx):
        if self._debug:
            print("if statement")
        # invent a new label, then push in the label stack
        if_ctx_end_if = self._prog.new_label("end_if")
        self.ctx_stack.append(if_ctx_end_if)
        raise NotImplementedError()
        # At the end, put the label and pop!
        self._prog.addLabel(if_ctx_end_if)
        popped = self.ctx_stack.pop()
        assert popped is if_ctx_end_if

    def visitWhileStat(self, ctx):
        if self._debug:
            print("while statement, condition is:")
            print(Trees.toStringTree(ctx.expr(), None, self._parser))
            print("and block is:")
            print(Trees.toStringTree(ctx.stat_block(), None, self._parser))
        raise NotImplementedError()

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
