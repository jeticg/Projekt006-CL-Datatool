# -*- coding: utf-8 -*-
# Python version: 2/3
#
# This script transforms a dependency tree loaded with natlang.format.conll
# Simon Fraser University
# Jetic Gu
#
from __future__ import print_function
from __future__ import absolute_import

import os
import sys
import copy
import inspect
import unittest
import progressbar

from natlang.loader import DataLoader
from natlang.format import conll


# Patter specification
# The pattern is a string with tree structure
# Here are some examples
#
#   ( * nsubj * | root | * advmod * )
#   This matches any tree with a subtree, the root of which has a nsubj as
#   leftChild and an advmod as right child
#
def parsePattern(pattern):
    bPattern = _parseStage1(pattern)
    return _parseStage2(bPattern)


def _parseStage1(pattern):
    def closeBrackets(pattern, startIndex=0):
        entry = []
        counter = 0
        i = startIndex
        while i < len(pattern):
            if pattern[i] == '(':
                counter += 1
                if counter > 1:
                    subEntry, i = closeBrackets(pattern, i)
                    entry.append(subEntry)
                    continue
            elif pattern[i] == ')':
                counter -= 1
                if counter < 0:
                    raise ValueError(
                        "natlang.analysis.conllTransformer.closeBrackets: " +
                        "invalid pattern, brackets not closed")
                if counter == 0:
                    return entry, i
            else:
                entry.append(pattern[i])
            i += 1
        if counter != 0:
            raise ValueError(
                "natlang.analysis.conllTransformer.closeBrackets: invalid " +
                "pattern, brackets not closed")
        return entry, i
    result = []
    counter = 0
    pattern =\
        pattern.replace('(', " ( ").replace(')', " ) ").replace('|', " | ")
    pattern = pattern.strip().split()
    if pattern[0] != '(':
        pattern = ['('] + pattern
        pattern = [')'] + pattern

    bPattern, _ = closeBrackets(pattern)
    return bPattern


def _parseStage2(bPattern):
    if bPattern == []:
        return []
    if isinstance(bPattern, str):
        return bPattern
    elements = [[]]
    for entry in bPattern:
        if entry == '|':
            elements.append([])
        elif isinstance(entry, list):
            subCPattern = _parseStage2(entry)
            elements[-1].append(subCPattern)
        else:
            elements[-1].append(entry)

    if len(elements) != 3:
        raise ValueError("numOfElements Incorrect")

    if (not isinstance(elements[1], list)) or len(elements[1]) != 1:
        raise ValueError("Invalid root specification")
    if not isinstance(elements[1][0], str):
        raise ValueError("Invalid root specification")

    cPattern = elements[1] + [elements[0], elements[2]]
    return cPattern


def matchPattern(pattern, node):
    # Value check
    if not isinstance(pattern, str):
        raise ValueError(
            "natlang.analysis.conllTransformer.matchPattern: pattern must " +
            "be a str")

    if not isinstance(node, conll.Node):
        raise ValueError(
            "natlang.analysis.conllTransformer.node: pattern must be a" +
            "natlang.format.conll.Node instance ")
    cPattern = parsePattern(pattern)
    if node.parent is None:
        # node is upper root
        candidates = _matchCPattern(cPattern, node.rightChild)
    else:
        candidates = _matchCPattern(cPattern, node)

    return candidates


def _matchCPattern(cPattern, node):
    if isinstance(cPattern, str):
        if cPattern == '*' or (node is not None and cPattern == node.deprel):
            return True
        else:
            print("root does not match", cPattern, node)
            return False
    # Match Root
    if cPattern[0] == '*' or cPattern[0] == node.deprel:
        if _matchCPatternChildren(cPattern[1], node.leftChild) and\
                _matchCPatternChildren(cPattern[2], node.rightChild):
            return True
    print("root does not match", cPattern, node)
    return False


# Match Children
def _matchCPatternChildren(childPattern, node):
    if childPattern == ['*'] or (childPattern == [] and node is None):
        return True
    if node is None:
        print("node is None", childPattern, node)
        return False

    # At this point, node is not None and childPattern has at least something
    if childPattern[0] == '*':
        if _matchCPatternChildren(childPattern[1:], node) or\
                _matchCPatternChildren(childPattern[1:], node.sibling):
            return True
        else:
            print("unable to match children", childPattern[1:], node)
            return False
    else:
        if not _matchCPattern(childPattern[0], node):
            print("unable to match entire node", childPattern[0], node)
            return False
        return _matchCPatternChildren(
            childPattern[1:], node.sibling)


class TestTree(unittest.TestCase):
    def testParseStage1A(self):
        content = _parseStage1("(closeBrackets(pattern))")
        answer = ["closeBrackets", ["pattern"]]
        self.assertSequenceEqual(content, answer)
        return

    def testParseStage1B(self):
        content = _parseStage1("( ( (9)  (16)  (9)  (19) ) )")
        answer = [[['9'], ['16'], ['9'], ['19']]]
        self.assertSequenceEqual(content, answer)
        return

    def testParseStage1C(self):
        content = _parseStage1(
            '( ( ( 5  (6)  (9)  4  (7) )  4  ( (17)  (10)  (1)  16  (4)  (0)' +
            '  (16)  10  2 )  7  2  1  ( (8)  (5)  3  (9)  (12)  15 )  ( (0)' +
            '  6  (1)  (11)  (17)  4 )  18  12 ) )')
        answer =\
            [[
                ['5', ['6'], ['9'], '4', ['7']], '4',
                [['17'], ['10'], ['1'], '16', ['4'], ['0'], ['16'], '10', '2'],
                '7', '2', '1',
                [['8'], ['5'], '3', ['9'], ['12'], '15'],
                [['0'], '6', ['1'], ['11'], ['17'], '4'], '18', '12']]
        self.assertSequenceEqual(content, answer)
        return

    def testParseStage1D(self):
        content = _parseStage1(
            '( ( (10)  (7)  11  (19)  17  (1)  (3) )  16  2 )')
        answer = [[['10'], ['7'], '11', ['19'], '17', ['1'], ['3']], '16', '2']
        self.assertSequenceEqual(content, answer)
        return

    def testParseStage2A(self):
        content = _parseStage2(
            _parseStage1("( * nsubj * | root | * advmod * )"))
        answer = ['root', ['*', 'nsubj', '*'], ['*', 'advmod', '*']]
        self.assertSequenceEqual(content, answer)
        return

    def testParseStage2B(self):
        content = _parseStage2(
            _parseStage1("( * (*|nsubj|*) * | root | * advmod * )"))
        answer = ['root',
                  ['*', ['nsubj', ['*'], ['*']], '*'],
                  ['*', 'advmod', '*']]
        self.assertSequenceEqual(content, answer)
        return

    def testMatch(self):
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        content = conll.load(parentdir + "/test/sampleCoNLLU.conll",
                             verbose=True)
        self.assertEqual(True, matchPattern("(* nsubj *|root|*)", content[0]))
        return


if __name__ == '__main__':
    if not bool(getattr(sys, 'ps1', sys.flags.interactive)):
        unittest.main()
