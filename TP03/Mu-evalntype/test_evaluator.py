#! /usr/bin/env python3
import pytest
import glob
import os
import sys
from test_expect_pragma import TestExpectPragmas

# tests for typing AND evaluation
# change here to also include bad_def tests.
ALL_FILES = glob.glob('ex/test*.mu')+glob.glob('ex-types/*.mu')


# Path setting
if 'TEST_FILES' in os.environ:
    ALL_FILES = glob.glob(os.environ['TEST_FILES'])
HERE = os.path.dirname(os.path.realpath(__file__))
MU_EVAL = os.path.join(HERE, 'Main.py')


class TestCodeGen(TestExpectPragmas):

    def evaluate(self, file):
        return self.run_command(['python3', MU_EVAL, file])

    @pytest.mark.parametrize('filename', ALL_FILES)
    def test_eval(self, filename):
        expect = self.get_expect(filename)
        eval = self.evaluate(filename)
        if expect:
            assert(expect == eval)


if __name__ == '__main__':
    pytest.main(sys.argv)
