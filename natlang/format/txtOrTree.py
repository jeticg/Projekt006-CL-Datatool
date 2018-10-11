# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Text and Tree loader
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
from tree import load as loadTree
from txt import load as loadTxt
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    try:
        contents = loadTree(file, linesToLoad)
        if len([f for f in contents if f is not None]) < (len(contents) / 2):
            return loadTxt(file, linesToLoad)
    except AttributeError:
        return loadTxt(file, linesToLoad)
    return contents
