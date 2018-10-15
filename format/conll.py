# -*- coding: utf-8 -*-
# Python version: 2/3
#
# CoNLL U data format
# Simon Fraser University
# Jetic Gu
#
from __future__ import print_function

import os
import sys
import copy
import unittest
import progressbar


defaultEntryIndex = {
    # This is taken from http://universaldependencies.org/format.html
    # CoNLL-U
    # item 8 and 9 are disabled
    "ID": 0,  # Word index, integer starting at 1 for each new sentence;
    "FORM": 1,  # Word form or punctuation symbol.
    "LEMMA": 2,  # Lemma or stem of word form.
    "UPOS": 3,  # Universal part-of-speech tag.
    "XPOS": 4,  # Language-specific part-of-speech tag; underscore if not
                # available.
    "FEATS": 5,  # List of morphological features from the universal feature
                 # inventory or from a defined language-specific extension;
                 # underscore if not available.
    "HEAD": 6,  # Head of the current word, which is either a value of ID or
                # zero (0).
    "DEPREL": 7,  # Universal dependency relation to the HEAD (root iff HEAD =
                  # 0) or a defined language-specific subtype of one.
    # "DEPS": 8,  # Enhanced dependency graph in the form of a list of
                # head-deprel pairs.
                # Note (Jetic): Universal dependencies don't use this at all.
    # "MISC": 9,  # Any other annotation.
    "__name__": "CoNLL U",
}

defaultCommentMark = '#'
_lArrow = u'\u250C'
_rArrow = u'\u2514'
_vArrow = u'\u2502'
_hArrow = u'\u2500'


class Node():
    '''
    This is the main data structure of a dependency, a Node instance is a node
    on the tree. The structure of the subtree with node x as root can be viewed
    by calling x.__repr__()
    '''
    def __init__(self, parent=None):
        self.value = ()
        self.phrase = []
        self.id = 0
        self.parent = parent
        self.deprel = ""
        self.leftChild = None
        self.rightChild = None
        self.sibling = None
        self.depth = -1
        self.format = "Unspecified"
        return

    def __repr__(self, __spacing=[], __showSibling=False):
        '''
        This method prints the structure of the subtree with self as root.
        '''
        if self.leftChild is not None:
            self.leftChild.__repr__(__spacing + [_lArrow], True)

        last = _rArrow
        for i, entry in enumerate(__spacing):
            if i == len(__spacing) - 1:
                print(entry, end='')
            elif (__spacing[i + 1] == _rArrow and entry == _lArrow) or\
                    (__spacing[i + 1] == _lArrow and entry == _rArrow):
                print(_vArrow + "       ", end='')
            else:
                print("        ", end='')
        if self.value == ("-ROOT-", ):
            print("ROOT")
        else:
            print(_hArrow + self.deprel + _hArrow + self.value[0])
        if self.rightChild is not None:
            self.rightChild.__repr__(__spacing + [_rArrow], True)

        if self.sibling is not None and __showSibling is True:
            self.sibling.__repr__(__spacing, True)
        return "\nRepresentation: " +\
            "conll.Node(\"" + str((self.id,) + self.value) + "\")\n" +\
            "Leafnode Label: " + str(self.phrase) + "\n"

    def __len__(self):
        return len(self.phrase)

    def export(self):
        raise NotImplementedError


def constructFromText(rawContent, entryIndex=defaultEntryIndex):
    content = [line.strip().split('\t') for line in rawContent]
    # adding the root node
    nodes = [Node()]
    nodes[0].value = ("-ROOT-", )

    for i, line in enumerate(content, start=1):
        # Check ID for data integrity
        if int(line[entryIndex["ID"]]) != i:
            sys.stderr.write(
                "natlang.format.conll [WARN]: Corrupt data format\n")
            return None

        # force the first value in node.value to be FORM
        # temporarily store parent id in node.parent
        # store everything else in node.value
        newNode = Node()
        if "__name__" in entryIndex:
            newNode.format = entryIndex["__name__"]
        newNode.id = i
        newNode.parent = int(line[entryIndex["HEAD"]])
        newNode.deprel = line[entryIndex["DEPREL"]]

        newNode.value = (line[entryIndex["FORM"]], )
        for i, item in enumerate(line):
            if i != entryIndex["ID"] and i != entryIndex["HEAD"] and\
                    i != entryIndex["DEPREL"]:
                newNode.value += (line[i], )

        nodes.append(newNode)

    # replace node.parent with real entity.
    # add sibling, leftChild, rightChild
    for node in nodes[1:]:
        node.parent = nodes[node.parent]
        if node.parent.id > node.id:
            # leftChild
            if node.parent.leftChild is None:
                node.parent.leftChild = node
                continue
            tmp = node.parent.leftChild
            while tmp.sibling is not None:
                tmp = tmp.sibling
            tmp.sibling = node
        else:
            # rightChild
            if node.parent.rightChild is None:
                node.parent.rightChild = node
                continue
            tmp = node.parent.rightChild
            while tmp.sibling is not None:
                tmp = tmp.sibling
            tmp.sibling = node

    return nodes[0]


def load(fileName,
         linesToLoad=sys.maxsize,
         entryIndex=defaultEntryIndex, commentMark=defaultCommentMark,
         verbose=False):
    fileName = os.path.expanduser(fileName)
    content = []
    widgets = [progressbar.Bar('>'), ' ', progressbar.ETA(),
               progressbar.FormatLabel(
               '; Total: %(value)d lines (in: %(elapsed)s)')]
    if verbose is False:
        loadProgressBar =\
            progressbar.ProgressBar(widgets=widgets,
                                    maxval=min(
                                        sum(1 for line in open(fileName)),
                                        linesToLoad)).start()
    i = 0
    entry = []
    for rawLine in open(fileName):
        i += 1
        if verbose is False:
            loadProgressBar.update(i)
        line = rawLine.strip()

        # Remove comments
        if line[0] == commentMark:
            continue

        if line == "":
            entry.append(line)
        else:
            content.append(constructFromText(entry))
            entry = []

        if i == linesToLoad and line == "":
            break

    if len(entry) > 0:
        content.append(constructFromText(entry))

    if verbose is False:
        loadProgressBar.finish()
    return content


class TestTree(unittest.TestCase):
    def testBuildTreeA(self, x=None):
        rawLine = [
            "1	From	from	ADP	IN	_	3	case	_	_",
            "2	the	the	DET	DT	Definite=Def|PronType=Art	3	det	_	_",
            "3	AP	AP	PROPN	NNP	Number=Sing	4	nmod	_	_",
            "4	comes	come	VERB	VBZ,	" +
            "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	0	root	_	_",
            "5	this	this	DET	DT	Number=Sing|PronType=Dem	6	det	_	_",
            "6	story	story	NOUN	NN	Number=Sing	4	nsubj	_	_",
            "7	:	:	PUNCT	:	_	4	punct	_	_]"]
        if x is None:
            x = constructFromText(rawLine)
        raise NotImplementedError
        return


if __name__ == '__main__':
    if not bool(getattr(sys, 'ps1', sys.flags.interactive)):
        unittest.main()
    else:
        rawLine = [
            "1	From	from	ADP	IN	_	3	case	_	_",
            "2	the	the	DET	DT	Definite=Def|PronType=Art	3	det	_	_",
            "3	AP	AP	PROPN	NNP	Number=Sing	4	nmod	_	_",
            "4	comes	come	VERB	VBZ,	" +
            "Mood=Ind|Number=Sing|Person=3|Tense=Pres|VerbForm=Fin	0	root	_	_",
            "5	this	this	DET	DT	Number=Sing|PronType=Dem	6	det	_	_",
            "6	story	story	NOUN	NN	Number=Sing	4	nsubj	_	_",
            "7	:	:	PUNCT	:	_	4	punct	_	_]"]
        x = constructFromText(rawLine)
        print("Use node x for testing new methods on Node.")
        print("Use unittest.main() to start unit test")
