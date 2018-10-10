# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Jetic's Text and Tree loader for NLP experiments.
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
import inspect
import unittest
currentdir =\
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)

from tree import loadPennTree
__version__ = "0.3a"


def load(file, linesToLoad=sys.maxsize):
    try:
        contents = loadPennTree(file, linesToLoad)
        if len([f for f in contents if f is not None]) < (len(contents) / 2):
            return loadText(file, linesToLoad)
    except AttributeError:
        return loadText(file, linesToLoad)
    return contents


def loadText(file, linesToLoad=sys.maxsize):
    return [line.strip().split() for line in open(os.path.expanduser(file))][
        :linesToLoad]
