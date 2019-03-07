from __future__ import absolute_import

import os
import unittest

import natlang as nl
from natlang.analysis import conllTransformer
from natlang.analysis import ner
from natlang.analysis import pos


def NER(lang="en", savedModel=None):
    return ner.Tagger(lang, savedModel)


def POS(lang="en", savedModel=None):
    return pos.Tagger(lang, savedModel)
