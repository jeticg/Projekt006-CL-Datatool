# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Dataset loader for NLP experiments.
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
import inspect
import unittest
import importlib
currentdir = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
if parentdir not in sys.path:
    sys.path.insert(0, parentdir)

__version__ = "0.3a"


class ParallelDataLoader():
    def __init__(self, srcFormat='txtOrTree', tgtFormat='txtOrTree'):
        self.srcLoader =\
            importlib.import_module("format." + srcFormat).load
        self.tgtLoader =\
            importlib.import_module("format." + tgtFormat).load
        return

    def load(self, fFile, eFile, linesToLoad=sys.maxsize):
        data = zip(self.srcLoader(fFile, linesToLoad),
                   self.tgtLoader(eFile, linesToLoad))
        # Remove incomplete or invalid entries
        data = [(f, e) for f, e in data if f is not None and e is not None]
        data = [(f, e) for f, e in data if len(f) > 0 and len(e) > 0]
        return data
