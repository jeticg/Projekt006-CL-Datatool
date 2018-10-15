import unittest
import natlang.format.AMR as AMR
import natlang.format.pyCode as pyCode
import natlang.format.semanticFrame as semanticFrame
import natlang.format.tree as tree
import natlang.format.txt as txt
import natlang.format.txtFiles as txtFiles
import natlang.format.txtOrTree as txtOrTree
import natlang.format.conll as conll


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
