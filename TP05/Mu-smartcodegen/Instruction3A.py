from Operands import (Operand, Immediate)

"""
MIF08, CAP, API TARGET18. 3A instruction constructors.
This file has one TODO for Lab5: dataflow analysis.
"""


def regset_to_string(registerset):
    """Utilitary function: pretty-prints a set of locations."""
    s = "{" + ",".join(str(x) for x in registerset) + "}"
    return s


class Instruction:
    """Real instruction, comment or label."""
    count = 0

    def __init__(self):
        self._i = Instruction.count
        self._isnotStart = True
        self._in = []
        self._out = []
        self._MAXOUT = 1  # Most blocks can have only one successor
        self._ins = None
        self._left = None
        self._right = None
        Instruction.count += 1
        # for liveness dataflow analysis (Lab 5)
        self._gen = set()  # should be initialised somewhere
        self._kill = set()

    def is_instruction(self):
        """True if the object is a true instruction (not a label or
        comment)."""
        return False

    def checkDep(self, visited):
        if self in visited:
            return False
        if self._in:
            for b in self._in:
                if b not in visited and b._i < self._i:
                    return False
            return True
        else:

            return True

    # Print an instruction, useful for lab "smartcodegen"
    def printIns(self, stream, visited, alloc):
        if self.checkDep(visited):
            visited.add(self)
            if self._ins:
                self._ins.printIns(stream, alloc)
            if self._out:
                # print("nb of childs="+str(len(self._out)))
                for child in self._out:
                    child.printIns(stream, visited, alloc)
        else:
            pass

    def printDot(self, graph, visited):
        """Prints the current block and its children."""
        if self.checkDep(visited):
            visited.add(self)
            if self._isnotStart:
                s1 = str(self._i) + "_" + str(self)
            else:
                s1 = "START"
            graph.add_node(s1)
            if self._out:
                for child in self._out:
                    s2 = str(child._i) + "_" + str(child)
                    graph.add_edge(s1, s2)
                    child.printDot(graph, visited)
        else:
            pass

    # Utility functions for dataflow analysis.

    def printGenKill(self):
        print("instr " + str(self._i) + ": " + str(self))
        print("gen: " + regset_to_string(self._gen))
        print("kill: " + regset_to_string(self._kill) + "\n")

        # DATAFLOW PROPAGATION for one node.
        # propagate dataflow information: update _gen and _kill sets (mapin,mapout)
        # and make a recursive call to its children.
    def do_dataflow_onestep(self, mapin, mapout, visited):
        """propagate dataflow information: update _gen and _kill sets
        (mapin,mapout) and make a recursive call to it children.

        visited is a set of already visited nodes.
        """
        if self.checkDep(visited):
            visited.add(self)
            i = self._i
            mapout[i] = set()  # new emptyset
            for child in self._out:
                mapout[i] = mapout[i].union(mapin[child._i])
                # update my _gen set
            mapin[i] = (mapout[i].difference(self._kill)).union(self._gen)
            for child in self._out:
                child.do_dataflow_onestep(mapin, mapout, visited)
        else:
            pass

    def update_defmap(self, defmap, visited):
        """Construct the map of blocks-> defs (=kill)."""
        if self.checkDep(visited):
            visited.add(self)
            i = self._i
            defmap[i] = self._kill
            for child in self._out:
                child.update_defmap(defmap, visited)
        else:
            pass


class Instru3A(Instruction):

    def __init__(self, ins, arg1=None, arg2=None, arg3=None, args=None):
        # A regular 3-address instruction has <=3 args, but compJUMP has 4.
        super().__init__()
        self._ins = ins
        if args:
            self.args = args
        else:
            self.args = [arg for arg in (arg1, arg2, arg3) if arg is not None]
        args = self.args
        self._left = args[0]
        if len(self.args) >= 3:
            self._right = (self.args[1], self.args[2])
        elif len(self.args) >= 2:
            self._right = (self.args[1],)
        for i in range(len(args)):
            if isinstance(args[i], int):
                args[i] = Immediate(args[i])
            assert isinstance(args[i], Operand), (args[i], type(args[i]))

    def is_instruction(self):
        """True if the object is a true instruction (not a label or
        comment)."""
        return True

    def get_name(self):
        return self._ins.lower()  # 2018 : asm doesn't like capital letters

    def is_read_only(self):
        """True if the instruction only reads from its operands.

        Otherwise, the first operand is considered as the destination
        and others are source.
        """
        return (self.get_name() == 'print'
                or self.get_name().startswith("print ")
                or self.get_name() == 'cmp'
                or self.get_name() == "jumpif"
                or self.get_name() == "jump")

    def __str__(self):
        s = self._ins
        for arg in self.args:
            s += ' ' + str(arg)
        return s

    def printIns(self, stream):
        """Print the instruction on the output."""
        print('       ', str(self), file=stream)

    def unfold(self):
        """Utility function to get both the instruction name and the operands
        in one call. Example:

        ins, args = i.unfold()
        """
        return self.get_name(), self.args


class Label(Instruction, Operand):
    """ A label is here a regular instruction"""

    def __init__(self, name, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._name = name

    def __str__(self):
        return ("lbl_{}".format(self._name))

    def printIns(self, stream):
        print(str(self) + ':', file=stream)


class Comment(Instruction):
    """ A comment is here a regular instruction"""

    def __init__(self, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._content = content

    def __str__(self):  # use only for printDot !
        return "comment"

    def printIns(self, stream):
        print('        ;; ' + self._content, file=stream)
