from __future__ import absolute_import

import unittest
from natlang.format import AMR
from natlang.format import pyCode
from natlang.format import semanticFrame
from natlang.format import tree
from natlang.format import txt
from natlang.format import txtFiles
from natlang.format import txtOrTree
from natlang.format import conll


modules = {
    AMR,
    pyCode,
    semanticFrame,
    tree,
    txt,
    txtFiles,
    txtOrTree,
    conll
}


def testSuite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite
    for module in modules:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite
