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


# Pattern specification (Dependency Expression V0.1a)
# The pattern is a string that works on a tree structure
# Here are some examples:
#
#   ( * nsubj * | root | * advmod * )
#   This matches any tree with a subtree, the root of which has a nsubj as
#   leftChild and an advmod as right child
#
#   ( * nsubj[UPOS=NN] * | root[UPOS!=VBZ] | * )
#   This matches any tree with a subtree, the root of which has a universal POS
#   tag that is not VBZ and a nsubj with universal POS tag NN as leftChild and
#   arbitrary number/types of rightChild.
def parsePattern(pattern):
    bPattern = _parseStage1(pattern)
    return _parseStage2(bPattern)


def _parseStage1(pattern):
    def closeBrackets(pattern, startIndex=0):
        entry = []
        counter = 0
        i = startIndex
        while i < len(pattern):
            # Process feature constraints
            if pattern[i] == '[':
                newEntry = ''
                while i < len(pattern):
                    newEntry += pattern[i]
                    i += 1
                    if i >= len(pattern):
                        raise ValueError(
                            "natlang.analysis.conllTransformer.closeBrackets" +
                            ": invalid pattern, [ not closed")
                    if pattern[i - 1] == ']':
                        break
                if len(entry) == 0 or not isinstance(entry[-1], str):
                    raise ValueError(
                        "natlang.analysis.conllTransformer.closeBrackets" +
                        ": invalid pattern, feature constraints can only " +
                        "follow dependency types (e.g. nsubj[UPOS=NN])")
                entry[-1] += newEntry

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
    pattern =\
        pattern.replace('[', " [ ").replace(']', " ] ").replace('*', " * ")
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
    candidates = []
    if node is None:
        return candidates
    if not isinstance(node, conll.Node):
        raise ValueError(
            "natlang.analysis.conllTransformer.matchPattern: node " +
            "must be a natlang.format.conll.Node instance")
    if matchPatternOnNode(pattern, node):
        candidates += [node]
    candidates += matchPattern(pattern, node.sibling)
    candidates += matchPattern(pattern, node.leftChild)
    candidates += matchPattern(pattern, node.rightChild)
    return candidates


def matchPatternOnNode(pattern, node):
    # Value check
    if not isinstance(pattern, str):
        raise ValueError(
            "natlang.analysis.conllTransformer.matchPatternOnNode: pattern " +
            "must be a str")

    if not isinstance(node, conll.Node):
        raise ValueError(
            "natlang.analysis.conllTransformer.matchPatternOnNode: pattern " +
            "must be a natlang.format.conll.Node instance")
    cPattern = parsePattern(pattern)
    return _matchCPattern(cPattern, node)


def _matchFeatureConstraints(dPattern, node):
    def constraintMet(constraint, node):
        if "!=" in constraint:
            constraint = constraint.split("!=").strip()
            matchEqual = False
        else:
            constraint = constraint.split("=").strip()
            matchEqual = True

        if len(constraint) != 2:
            raise ValueError(
                "natlang.analysis.conllTransformer." +
                "_matchFeatureConstraints:" +
                " invalid feature constraint")
        key, value = constraint[0], constraint[1]
        if key not in node.format:
            raise ValueError(
                "natlang.analysis.conllTransformer." +
                "_matchFeatureConstraints:" +
                " invalid feature constraint: feature entry not found in" +
                " node format")
        if matchEqual:
            return value != node.rawEntries[node.format[key]]
        else:
            return value == node.rawEntries[node.format[key]]

    if '[' not in dPattern:
        if dPattern == '*' or (node is not None and dPattern == node.deprel):
            return True
        else:
            return False
    else:
        constraints = dPattern.replace('[', '°').replace(']', '').split('°')
        if len(constraints) != 2:
            raise ValueError(
                "natlang.analysis.conllTransformer._matchFeatureConstraints:" +
                " invalid feature constraint")
        deprel, constraints = constraints[0], constraints[1]
        constraints = constraints.split(';')
        for constraint in constraints:
            if not constraintMet(constraint, node):
                return False
        return True


def _matchCPattern(cPattern, node):
    if isinstance(cPattern, str):
        if cPattern == '*' or (node is not None and cPattern == node.deprel):
            return True
        else:
            return False
    # Match Root
    if cPattern[0] == '*' or cPattern[0] == node.deprel:
        if _matchCPatternChildren(cPattern[1], node.leftChild) and\
                _matchCPatternChildren(cPattern[2], node.rightChild):
            return True
    return False


# Match Children
def _matchCPatternChildren(childPattern, node):
    if childPattern == ['*'] or (childPattern == [] and node is None):
        return True
    if node is None:
        return False

    # At this point, node is not None and childPattern has at least something
    if childPattern[0] == '*':
        if _matchCPatternChildren(childPattern[1:], node) or\
                _matchCPatternChildren(childPattern[1:], node.sibling):
            return True
        else:
            return False
    else:
        if not _matchCPattern(childPattern[0], node):
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

    def testParseStage1E(self):
        answer = ['*', 'nsubj[POS=NN]', '*', 'cop', '*', '|', 'root[POS=VBZ]',
                  '|', '*']
        content = _parseStage1("(*nsubj[POS=NN]*cop*|root[POS=VBZ]|*)")
        self.assertSequenceEqual(content, answer)
        content = _parseStage1("(* nsubj[POS=NN] * cop * |root[POS=VBZ]|*)")
        self.assertSequenceEqual(content, answer)
        content = _parseStage1("(* nsubj [ POS = NN ] * cop * |root [ POS = " +
                               "VBZ ]|*)")
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

    def testMatchNode1(self):
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        content = conll.load(parentdir + "/test/sampleCoNLLU.conll",
                             verbose=True)
        self.assertEqual(
            True,
            matchPatternOnNode("(*|root|* nsubj *)", content[0].rightChild))
        return

    def testMatchNode2(self):
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        content = conll.load(parentdir + "/test/sampleCoNLLU.conll",
                             verbose=True)
        self.assertEqual(
            False,
            matchPatternOnNode("(* nsubj *|root|*)", content[0].rightChild))
        return

    def testMatchGeneral1(self):
        currentdir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe())))
        parentdir = os.path.dirname(currentdir)
        content = conll.load(parentdir + "/test/sampleCoNLLU.conll",
                             verbose=True)
        self.assertEqual(
            [content[0].rightChild],
            matchPattern("(*|root|* nsubj *)", content[0]))

        match1 = matchPattern("(case *|nmod|*)", content[1])

        self.assertEqual(3, len(match1))
        self.assertSequenceEqual(
            [4, 14, 18], sorted([item.id for item in match1]))
        return


if __name__ == '__main__':
    if not bool(getattr(sys, 'ps1', sys.flags.interactive)):
        unittest.main()
