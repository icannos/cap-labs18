#! /usr/bin/env python3

import pytest
import glob
import os
import sys
import subprocess
import Main
from Operands import AllocationError
from test_expect_pragma import TestExpectPragmas

"""
Usage:
    python3 test_codegen.py
(or make tests)
"""

"""
MIF08 and CAP, 2018
Unit test infrastructure for testing code generation:
1) compare the actual output to the expected one (in comments)
2) compare the actual output to the one obtained by simulation
3) for different allocation algorithms
"""

onlyNaive = False  # change here to only test wrt the naive allocator.
withEval = True  # change here if your evaluator is too buggy.

# change here for step2, and your own test files
ALL_FILES = glob.glob('tests/step1/*.mu')

HERE = os.path.dirname(os.path.realpath(__file__))

TARGETM = os.path.join(HERE, '..', '..', 'target18')

ASM = os.path.join(TARGETM, '.', 'asm.py')
SIMU = os.path.join(TARGETM, 'emu', 'emu')

MU_EVAL = os.path.join(
HERE, '..', '..', 'TP03', 'Mu-evalntype', 'Main.py')


class TestCodeGen(TestExpectPragmas):
    def evaluate(self, file):
        if withEval:
            return subprocess.check_output([
                'python3',
                MU_EVAL,
                file]).decode("utf-8", "strict")
        else:
            pass

    def naive_alloc(self, file):
        return self.compile_and_simulate(file, naive_alloc=True)

    def all_in_mem(self, file):
        return self.compile_and_simulate(file, all_in_mem=True)

    def compile_and_simulate(self, file, naive_alloc=False, all_in_mem=False):
        basename, rest = os.path.splitext(file)
        print("Compiling ...")
        if naive_alloc:
            output_base = basename + '-naive'
        elif all_in_mem:
            output_base = basename + '-allinmem'
        else:
            output_base = basename
        output_name = output_base + '.s'
        self.remove(output_name)
        try:
            Main.main(file,
                      output_name=output_name,
                      naive_alloc=naive_alloc,
                      all_in_mem=all_in_mem)
        except AllocationError:
            if naive_alloc:
                pytest.skip("Too big for the naive allocator")
            else:
                raise Exception("AllocationError should only happen "
                                "for naive_alloc=true")
        assert(os.path.isfile(output_name))
        print("Compiling ... OK")
        if naive_alloc or all_in_mem:  # Only executable code!
            sys.stderr.write("Assembling " + output_name + " ... ")
            self.remove(output_base + '.bin')
            cmd = [
                'python3', ASM, '-b', output_name,
                '-o', output_base + '.bin'
            ]
            subprocess.check_output(cmd)
            assert(os.path.isfile(output_base + '.bin'))
            sys.stderr.write("Assembling ... OK\n")
            try:
                return subprocess.check_output(
                    [SIMU,
                     # If needed, uncomment the following to change
                     # the memory layout:
                     # '--geometry', '32k:16k:16k:327680',
                     '-r', output_base + '.bin'],
                    timeout=10).decode("utf-8", "strict")
            except subprocess.TimeoutExpired:
                pytest.fail()
            except subprocess.CalledProcessError as e:
                pytest.fail("Emulator failed for command {}.\nOutput:{}\n".format(
                    ' '.join(e.cmd), e.output.decode('utf-8')))
        else:
            return None

    @pytest.mark.parametrize('filename', ALL_FILES)
    @pytest.mark.skipif(not withEval, reason='withEval is True')
    def test_expect(self, filename):
        """Test the EXPECTED annotations in test files by launching the interpreter."""
        expect = self.get_expect(filename).output
        evalval = self.evaluate(filename)
        if expect:
            assert(expect == evalval)

    # @pytest.mark.parametrize('filename', ALL_FILES)
    # def test_compile_and_simulate(self, filename):
    #     """Just generate 3 address code. It does not simulate."""
    #     expect = self.get_expect(filename)
    #     actual = self.compile_and_simulate(filename)
    #     assert actual is None

    @pytest.mark.parametrize('filename', ALL_FILES)
    def test_naive_alloc(self, filename):
        expect = self.get_expect(filename).output
        naive = self.naive_alloc(filename)
        if expect and naive is not None:
            assert naive == expect

    @pytest.mark.parametrize('filename', ALL_FILES)
    @pytest.mark.skipif(onlyNaive, reason="onlyNaive is False")
    def test_alloc_mem(self, filename):
        expect = self.get_expect(filename).output
        mem = self.all_in_mem(filename)
        if expect:
            assert mem == expect


if __name__ == '__main__':
    pytest.main(sys.argv)
