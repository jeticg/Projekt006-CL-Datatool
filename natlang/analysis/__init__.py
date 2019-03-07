from __future__ import absolute_import

import unittest
import natlang as nl
from natlang.analysis import conllTransformer
from natlang.analysis import ner


def NER(lang="en", savedModel=None):
    return ner.Tagger(lang, savedModel)
