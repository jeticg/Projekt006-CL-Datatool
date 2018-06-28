# -*- coding: utf-8 -*-
# Python version: 2
#
# Jetic's dataset loader for NLP experiments.
# Simon Fraser University
# Jetic Gu
#
#
import os
import sys
import inspect
import unittest
from tree import loadPennTree, Node
__version__ = "0.1a"


def _loadBitext(file1, file2, linesToLoad=sys.maxsize):
    '''
    This function is used to read a bitext from two text files.

    @param file1: str, the first file to read
    @param file2: str, the second file to read
    @param* linesToLoad: int, the lines to read
    @return: Bitext, detailed of this format:
        https://github.com/sfu-natlang/HMM-Aligner/wiki/API-reference:-Dataset-Data-Format-V0.1a#bitext
    '''
    path1 = os.path.expanduser(file1)
    path2 = os.path.expanduser(file2)
    bitext =\
        [[sentence.strip().split() for sentence in pair] for pair in
            list(zip(open(path1), open(path2)))[:linesToLoad]]
    return bitext


def loadDataset(fFiles, eFiles, linesToLoad=sys.maxsize,
                reverse=False):
    '''
    This function is used to read a Dataset files.

    @param fFiles: list of str, the file containing source language files,
        including FORM, POS, etc.,
    @param eFiles: list of str, the file containing target language files,
        including FORM, POS, etc.,
    @param alignmentFile: str, the alignmentFile
    @param* linesToLoad: int, the lines to read
    @return: Dataset, detail of this format:
        https://github.com/sfu-natlang/HMM-Aligner/wiki/API-reference:-Dataset-Data-Format-V0.2a#tritext
    '''
    fContents =\
        [list(zip(*[fContent.strip().split() for fContent in contents]))
         for contents in list(zip(*[open(os.path.expanduser(fFile))
                                    for fFile in fFiles]))[:linesToLoad]]
    eContents =\
        [list(zip(*[eContent.strip().split() for eContent in contents]))
         for contents in list(zip(*[open(os.path.expanduser(eFile))
                                    for eFile in eFiles]))[:linesToLoad]]

    return zip(fContents, eContents)


def loadTreeDataset(fFile, eFile, linesToLoad=sys.maxsize):
    try:
        fContents = loadPennTree(fFile, linesToLoad)
        if len([f for f in fContents if f is not None]) < (len(fContents) / 2):
            fContents =\
                [line.strip().split()
                 for line in open(os.path.expanduser(fFile))][:linesToLoad]
    except AttributeError:
        fContents =\
            [line.strip().split() for line in open(os.path.expanduser(fFile))][
                :linesToLoad]
    eContents = loadPennTree(eFile, linesToLoad)
    dataset = zip(fContents, eContents)
    dataset = [(f, e) for f, e in dataset if f is not None and e is not None]
    dataset = [(f, e) for f, e in dataset if len(f) > 0 and len(e) > 0]

    return dataset


def exportToFile(result, fileName):
    try:
        outputFile = open(fileName, "w")
    except IOError:
        os.system("kinit")
        outputFile = open(fileName, "w")

    for sent in result:
        if isinstance(sent, Node):
            line = sent.export()
        else:
            line = " ".join(sent)
        outputFile.write(line + "\n")
    outputFile.close()
    return


class RealtimeExporter():
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
