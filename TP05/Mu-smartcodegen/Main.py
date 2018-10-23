#! /usr/bin/env python3
"""
Lab 5 Main File. Code Generation with Smart IRs.
Usage:
    python3 Main.py <filename>
"""
from MuLexer import MuLexer
from MuParser import MuParser
from MuCodeGen3AVisitor import MuCodeGen3AVisitor
from ExpandJump import replace_all_meta

import argparse

from antlr4 import FileStream, CommonTokenStream

import os

debug = False  # Should be False in your final version+make tests


def main(inputname, stdout=False, output_name=None):
    (hd, rest) = os.path.splitext(inputname)
    if stdout:
        output_name = None
        print("Code will be generated on standard output")
    else:
        output_name = hd + ".s"
        print("Code will be generated in file " + output_name)

    input_s = FileStream(inputname)
    lexer = MuLexer(input_s)
    stream = CommonTokenStream(lexer)
    parser = MuParser(stream)
    tree = parser.prog()

    # Codegen 3@ CFG Visitor, first argument is debug mode
    visitor3 = MuCodeGen3AVisitor(debug, parser)

    visitor3.visit(tree)
    prog = visitor3.get_prog()

    # prints the CFG as a dot file
    if debug:
        prog.printDot(hd + ".dot")
        print("CFG generated in " + hd + ".dot.pdf")

    # TODO: Move the print&return statements below down as you progress
    # TODO: in the lab. They must be removed from the final version.
    print("Stopping here for now")
    return

    # dataflow
    if debug:
        prog.printGenKill()

    mapin, mapout = prog.doDataflow()
    if debug:
        prog.printMapInOut()

    # conflict graph
    igraph = prog.doInterfGraph()

    if debug:
        print("printing the conflict graph")
        igraph.print_dot(hd + "_conflicts.dot")

    replace_all_meta(prog)  # replace conditional jump in the 3@code

    # Smart Alloc via graph coloring
    prog.smart_alloc(debug, hd + "_colored.dot")
    prog.printCode(output_name, comment="Smart Allocation")
    if debug:
        visitor3.printRegisterMap()  # print allocation


# Now only smart allocation!
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate code for .mu file')
    parser.add_argument('filename', type=str,
                        help='Source file.')
    parser.add_argument('--stdout', action='store_true',
                        help='Generate code to stdout')
    parser.add_argument('--output', type=str,
                        help='Generate code to outfile')

    args = parser.parse_args()
    main(args.filename, args.stdout, args.output)
