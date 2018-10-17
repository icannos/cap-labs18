#! /usr/bin/env python3
"""
Usage:
    python3 Main.py <filename>
    python3 Main.py --three-addr <filename>
"""
from MuLexer import MuLexer
from MuParser import MuParser
from MuCodeGen3AVisitor import MuCodeGen3AVisitor
from ExpandJump import replace_all_meta

import argparse

from antlr4 import FileStream, CommonTokenStream
from os import path

# Lab 5 CAP, syntax-directed code generation.
#  At the end, debug should be False
debug = True


def main(inputname, stdout=False, output_name=None,
         naive_alloc=False, all_in_mem=False):
    if stdout:
        output_name = None
    else:
        if output_name is None:
            (hd, rest) = path.splitext(inputname)
            output_name = hd + ".s"
        print("Code will be generated in file " + output_name)

    input_s = FileStream(inputname)
    lexer = MuLexer(input_s)
    stream = CommonTokenStream(lexer)
    parser = MuParser(stream)
    tree = parser.prog()
    if debug:
        print("Generation of 3 address code.")

    # Construction of the 3-adress program
    visitor3 = MuCodeGen3AVisitor(debug, output_name, parser)
    visitor3.visit(tree)
    prog = visitor3.get_prog()
    replace_all_meta(prog)

    # Allocation part
    if naive_alloc:
        prog.naive_alloc()
        comment = "naive allocation"
    elif all_in_mem:
        prog.alloc_to_mem()
        comment = "all-in-memory allocation"
    else:
        comment = "non executable 3-Address instructions"
        pass
    if debug:
        print("now dump the code with: " + comment)

    # Now prints the output .s file
    prog.printCode(output_name, comment=comment)
    if debug:
        visitor3.printRegisterMap()  # print decs.


# command line management
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Generate code for .mu file')
    parser.add_argument('filename', type=str,
                        help='Source file.')
    parser.add_argument('--naive-alloc', action='store_true',
                        help='Perform naive register allocation after'
                        '3@-code generation.')
    parser.add_argument('--all-in-mem', action='store_true',
                        help='store all temporaries to memory.')
    parser.add_argument('--stdout', action='store_true',
                        help='Generate code to stdout')
    parser.add_argument('--output', type=str,
                        help='Generate code to outfile')

    args = parser.parse_args()
    main(args.filename, args.stdout, args.output,
         args.naive_alloc, args.all_in_mem)
