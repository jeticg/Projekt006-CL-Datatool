# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Dataset exporter.
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
import inspect
import unittest
from .format.tree import Node
__version__ = "0.3a"


def exportToFile(result, fileName):
    with open(fileName, "w") as outputFile:
        for sent in result:
            if isinstance(sent, Node):
                line = sent.export()
            else:
                line = " ".join(sent)
            outputFile.write(line + "\n")
    return


class RealtimeExporter():
    """
    Use this class to export in real time.
    """
    def __init__(self, fileName):
        self.__outputFile = open(fileName, "w")
        return

    def write(self, sent):
        if isinstance(sent, Node):
            line = sent.export()
        else:
            line = " ".join(sent)
        self.__outputFile.write(line + "\n")
        self.__outputFile.flush()
        return

    def __del__(self):
        if self.__outputFile:
            self.__outputFile.close()
