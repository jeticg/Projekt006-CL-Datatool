from __future__ import absolute_import

import unittest
from . import AMR
from . import pyCode
from . import semanticFrame
from . import tree
from . import txt
from . import txtFiles
from . import txtOrTree
from . import conll


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
