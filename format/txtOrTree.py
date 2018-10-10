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
from tree import load
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    try:
        contents = load(file, linesToLoad)
        if len([f for f in contents if f is not None]) < (len(contents) / 2):
            return loadText(file, linesToLoad)
    except AttributeError:
        return loadText(file, linesToLoad)
    return contents


def loadText(file, linesToLoad=sys.maxsize):
    return [line.strip().split() for line in open(os.path.expanduser(file))][
        :linesToLoad]
