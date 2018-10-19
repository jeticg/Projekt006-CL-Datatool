# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Dataset loader for NLP experiments.
# Simon Fraser University
# Jetic Gu
#
#
from __future__ import absolute_import
import os
import sys
import inspect
import unittest
import glob
import importlib

from natlang.format import *

__version__ = "0.3a"

supportedList = {
    "tree": tree,
    "txtFiles": txtFiles,
    "txt": txt,
    "AMR": AMR,
    "txtOrTree": txtOrTree,
    "pyCode": pyCode,
    "conll": conll,
    "semanticFrame": semanticFrame,
}


class DataLoader():
    def __init__(self, format="txtOrTree"):
        if isinstance(format, str):
            if format not in supportedList:
                raise ValueError(
                    "natlang.dataLoader.load: invalid format selection")
            else:
                self.loader = supportedList[format].load
        else:
            if hasattr(obj, '__call__'):
                self.loader = format
            else:
                raise ValueError(
                    "natlang.dataLoader.load: custom format selected not " +
                    "callable")
        return

    def load(self, file, linesToLoad=sys.maxsize, verbose=False):
        def matchPattern(pattern):
            return [filename
                    for filename in glob.glob(os.path.expanduser(pattern))
                    if os.path.isfile(filename)]

        content = []
        if isinstance(file, list):
            files = []
            for filePattern in file:
                files += matchPattern(filePattern)
        elif isinstance(file, str):
            files = matchPattern(file)
        else:
            raise RuntimeError("natlang.dataLoader.load [ERROR]: parameter " +
                               "type")

        if len(files) == 0:
            raise RuntimeError(
                "natlang.dataLoader.load [ERROR]: Cannot find matching files")

        if sys.version_info[0] < 3:
            getSpec = inspect.getargspec
        else:
            getSpec = inspect.getfullargspec
        if "verbose" in getSpec(self.loader)[0]:
            for filename in files:
                content += self.loader(filename,
                                       linesToLoad=linesToLoad,
                                       verbose=verbose)
        else:
            for filename in files:
                content += self.loader(filename, linesToLoad=linesToLoad)
        return content


class ParallelDataLoader():
    def __init__(self,
                 srcFormat="txtOrTree",
                 tgtFormat="txtOrTree",
                 verbose=False):
        self.srcLoader = DataLoader(srcFormat)
        self.tgtLoader = DataLoader(tgtFormat)
        return

    def load(self, fFile, eFile, linesToLoad=sys.maxsize):
        data = zip(self.srcLoader.load(fFile, linesToLoad),
                   self.tgtLoader.load(eFile, linesToLoad))
        # Remove incomplete or invalid entries
        data = [(f, e) for f, e in data if f is not None and e is not None]
        data = [(f, e) for f, e in data if len(f) > 0 and len(e) > 0]
        return data
