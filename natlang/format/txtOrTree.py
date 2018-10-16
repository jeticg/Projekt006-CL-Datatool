# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Text and Tree loader
# Simon Fraser University
# Jetic Gu
#
#
from __future__ import absolute_import
import os
import sys
try:
    from tree import load as loadTree
    from txt import load as loadTxt
except ImportError:
    from .tree import load as loadTree
    from .txt import load as loadTxt
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    try:
        contents = loadTree(file, linesToLoad)
        contentsTxt = loadTxt(file, linesToLoad)
        if len([f for f in contents if f is not None]) <\
                (len(contentsTxt) / 2):
            return contentsTxt
    except AttributeError:
        return loadTxt(file, linesToLoad)
    return contents
