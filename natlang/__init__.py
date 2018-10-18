from __future__ import absolute_import
import unittest

from natlang import format
from natlang import analysis

from natlang import exporter
from natlang import fileConverter
from natlang import loader

from natlang import version

testModules = {
    format.AMR,
    format.pyCode,
    format.semanticFrame,
    format.tree,
    format.txt,
    format.txtFiles,
    format.txtOrTree,
    format.conll,
    analysis.conllTransformer
}


def testSuite():
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # add tests to the test suite
    for module in testModules:
        suite.addTests(loader.loadTestsFromModule(module))
    return suite


name = "natlang"
