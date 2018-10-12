from MuVisitor import MuVisitor
from MuParser import MuParser

from enum import Enum


class MuTypeError(Exception):
    pass


class BaseType(Enum):
    Float, Integer, Boolean, String, Nil = range(5)

    def printBaseType(self):
        print(self)


# Basic Type Checking for Mu programs.
class MuTypingVisitor(MuVisitor):

    def __init__(self):
        self._memorytypes = dict()  # id-> types

    def _raise(self, ctx, for_what, *types):
        raise MuTypeError(
            'Line {} col {}: invalid type for {}: {}'.format(
                ctx.start.line, ctx.start.column, for_what,
                ' and '.join(t.name.lower() for t in types)))

    # type declaration

    def visitVarDecl(self, ctx):
        raise NotImplementedError()

    def visitBasicType(self, ctx):
        if ctx.mytype.type == MuParser.INTTYPE:
            return BaseType.Integer
        elif ctx.mytype.type == MuParser.FLOATTYPE:
            return BaseType.Float
        else:  # TODO: same for other types
            raise NotImplementedError()

    def visitIdList(self, ctx):
        raise NotImplementedError()

    def visitIdListBase(self, ctx):
        raise NotImplementedError()

    # typing visitors for expressions, statements !

    # visitors for atoms --> value
    def visitParExpr(self, ctx):
        return self.visit(ctx.expr())

    def visitNumberAtom(self, ctx):
        s = ctx.getText()
        try:
            int(s)
            return BaseType.Integer
        except ValueError:
            try:
                float(s)
                return BaseType.Float
            except ValueError:
                raise MuTypeError("Invalid number atom")

    def visitBooleanAtom(self, ctx):
        raise NotImplementedError()

    def visitIdAtom(self, ctx):
        try:
            valtype = self._memorytypes[ctx.getText()]
            return valtype
        except KeyError:
            raise MuTypeError("Undefined variable {}".format(ctx.getText()))

    def visitStringAtom(self, ctx):
        return BaseType.String

    def visitNilAtom(self, ctx):
        return BaseType.Nil

    # now visit expr

    def visitAtomExpr(self, ctx):
        return self.visit(ctx.atom())

    def visitOrExpr(self, ctx):
        raise NotImplementedError()

    def visitAndExpr(self, ctx):
        raise NotImplementedError()

    def visitEqualityExpr(self, ctx):
        raise NotImplementedError()

    def visitRelationalExpr(self, ctx):
        raise NotImplementedError()

    def visitAdditiveExpr(self, ctx):
        raise NotImplementedError()

    def visitMultiplicativeExpr(self, ctx):
        raise NotImplementedError()

    def visitNotExpr(self, ctx):
        raise NotImplementedError()

    def visitUnaryMinusExpr(self, ctx):
        raise NotImplementedError()

    def visitPowExpr(self, ctx):
        raise NotImplementedError()

    # statements
    def visitAssignStat(self, ctx):
        raise NotImplementedError()

    def visitCondBlock(self, ctx):
        raise NotImplementedError()

    def visitWhileStat(self, ctx):
        raise NotImplementedError()

    def visitIfStat(self, ctx):
        raise NotImplementedError()

