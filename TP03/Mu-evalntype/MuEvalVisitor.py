from MuVisitor import MuVisitor
from MuParser import MuParser

# Visitor to *interpret* Mu files


class MuRuntimeError(Exception):
    pass


class MuSyntaxError(Exception):
    pass


class MuEvalVisitor(MuVisitor):

    def __init__(self):
        self._memory = dict()  # store all variable ids and values.

    # visitors for variable declarations

    def visitVarDecl(self, ctx):
        # Initialise all variables in self._memory (toto |-> None)
        pass

    def visitIdList(self, ctx):
        pass

    def visitIdListBase(self, ctx):
        return [ctx.ID().getText()]

    # visitors for atoms --> value
    # this code is given to students except for idatoms !

    def visitParExpr(self, ctx):
        return self.visit(ctx.expr())

    def visitNumberAtom(self, ctx):
        s = ctx.getText()
        try:
            return int(s)
        except ValueError:
            return float(s)

    def visitBooleanAtom(self, ctx):
        return ctx.getText() == "true"

    def visitIdAtom(self, ctx):
        pass

    def visitStringAtom(self, ctx):
        return ctx.getText()[1:-1]

    def visitNilAtom(self, ctx):
        return ctx.getText()

    # visit expressions
    # this code is given to students
    def visitAtomExpr(self, ctx):
        return self.visit(ctx.atom())

    def visitOrExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        return lval | rval

    def visitAndExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        return lval & rval

    def visitEqualityExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        # be careful for float equality
        if ctx.myop.type == MuParser.EQ:
            return lval == rval
        else:
            return lval != rval

    def visitRelationalExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        if ctx.myop.type == MuParser.LT:
            return lval < rval
        elif ctx.myop.type == MuParser.LTEQ:
            return lval <= rval
        elif ctx.myop.type == MuParser.GT:
            return lval > rval
        elif ctx.myop.type == MuParser.GTEQ:
            return lval >= rval
        else:
            raise MuSyntaxError("Unknown comparison operator '%s'" % ctx.myop)

    def visitAdditiveExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        if ctx.myop.type == MuParser.PLUS:
            if any(isinstance(x, str) for x in (lval, rval)):
                return '{}{}'.format(lval, rval)
            else:
                return lval + rval
        elif ctx.myop.type == MuParser.MINUS:
            return lval - rval
        else:
            raise MuSyntaxError("Unknown additive operator '%s'" % ctx.myop)

    def visitMultiplicativeExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        if ctx.myop.type == MuParser.MULT:
            return lval * rval
        elif ctx.myop.type == MuParser.DIV:
            return lval / rval
        elif ctx.myop.type == MuParser.MOD:
            return lval % rval
        else:
            raise MuSyntaxError("Unknown multiplication operator '%s'"
                                % ctx.myop)

    def visitNotExpr(self, ctx):
        return not self.visit(ctx.expr())

    def visitUnaryMinusExpr(self, ctx):
        return -self.visit(ctx.expr())

    def visitPowExpr(self, ctx):
        lval = self.visit(ctx.expr(0))
        rval = self.visit(ctx.expr(1))
        return lval ** rval

    # visit statements

    def visitLogStat(self, ctx):
        val = self.visit(ctx.expr())
        if isinstance(val, bool):
            val = '1' if val else '0'
        if isinstance(val, float):
            val = "%.2f" % val
        print(val)

    def visitAssignStat(self, ctx):
        pass

    def visitCondBlock(self, ctx):
        # expr bool, then stat-block
        # exec the stat-block and return true if the cond evaluates to true
        # else return False.
        pass

    def visitIfStat(self, ctx):
        pass

    def visitWhileStat(self, ctx):
        pass

