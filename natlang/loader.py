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
import ast
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
                    "natlang.dataLoader: invalid format selection")
            else:
                self.loader = supportedList[format].load
        else:
            if hasattr(obj, '__call__'):
                self.loader = format
            else:
                raise ValueError(
                    "natlang.dataLoader: custom format selected not " +
                    "callable")
        return

    def load(self, file, linesToLoad=sys.maxsize, verbose=True, option={}):
        if isinstance(option, str):
            if '{' in option and '}' in option:
                option = ast.literal_eval(option)
            else:
                option = option.split('=')
                if len(option) == 1:
                    option = {option[0]:True}
                elif len(option) == 2:
                    option = dict([option])
                else:
                    raise ValueError(
                        "natlang.dataLoader.load: invalid option")
        if option is None:
            option = {}
        if not isinstance(option, dict):
            raise ValueError(
                "natlang.dataLoader.load: invalid option")
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
            if "option" in getSpec(self.loader)[0]:
                load = lambda fileName: self.loader(filename,
                                                    linesToLoad=linesToLoad,
                                                    verbose=verbose,
                                                    option=option)
            else:
                load = lambda fileName: self.loader(filename,
                                                    linesToLoad=linesToLoad,
                                                    verbose=verbose)
        else:
            if "option" in getSpec(self.loader)[0]:
                load = lambda fileName: self.loader(filename,
                                                    linesToLoad=linesToLoad,
                                                    option=option)
            else:
                load = lambda fileName: self.loader(filename,
                                                    linesToLoad=linesToLoad)

        for filename in files:
            content += load(filename)
        return content


class ParallelDataLoader():
    def __init__(self,
                 srcFormat="txtOrTree",
                 tgtFormat="txtOrTree",
                 verbose=True):
        self.srcLoader = DataLoader(srcFormat)
        self.tgtLoader = DataLoader(tgtFormat)
        return

    def load(self, fFile, eFile,
             linesToLoad=sys.maxsize, verbose=True, option={}):
        data = zip(self.srcLoader.load(fFile, linesToLoad,
                                       verbose=verbose, option=option),
                   self.tgtLoader.load(eFile, linesToLoad,
                                       verbose=verbose, option=option))
        # Remove incomplete or invalid entries
        data = [(f, e) for f, e in data if f is not None and e is not None]
        data = [(f, e) for f, e in data if len(f) > 0 and len(e) > 0]
        return data
