# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Model Base for Sequential Models
# Simon Fraser University
# Jetic Gu
#
# Modified from Jetic's CodeGen-Experiments' src/models/ModelBase.py
# (commit: 81b5b3d)
#
import os
import errno
import gzip
import pickle as pickle

from natlang.format.conll import Node


class ModelBase:
    def __init__(self):
        self.inDim = 0
        self.hidDim = 0
        self.layers = 0
        self.component = []
        return

    def loadModel(self, fileName=None, force=False):
        fileName = os.path.expanduser(fileName)
        if fileName.endswith("pklz"):
            pklFile = gzip.open(fileName, 'rb')
        else:
            pklFile = open(fileName, 'rb')

        entity = vars(self)
        # load components
        for componentName in self.component:
            if componentName not in entity:
                raise RuntimeError("object " + componentName +
                                   " doesn't exist in this class")
            entity[componentName] = self.__loadObjectFromFile(pklFile)

        pklFile.close()
        return

    def buildLexicon(self, dataset, entry="FORM", lexiconSize=50000):
        w2int = {}
        int2w = []
        for sample in dataset:
            if not isinstance(sample, Node):
                raise RuntimeError("Invalid data type: must be conll node")
            for node in sample.phrase:
                if entry not in node.format:
                    raise RuntimeError("entry not covered in data format")
                word = node.rawEntries[node.format[entry]]
                if word not in w2int:
                    w2int[word] = 0
                w2int[word] += 1

        lex =\
            sorted(list(w2int.items()), key=lambda y: y[1])[-lexiconSize:]
        w2int = dict(lex)
        w2int["<UNK>"] = 0
        for key in w2int:
            w2int[key] = len(int2w)
            int2w.append(key)
        return w2int, int2w

    def convertDataset(self, dataset, entry, w2int):
        for sample in dataset:
            if not isinstance(sample, Node):
                raise RuntimeError("Invalid data type: must be conll node")
            for node in sample.phrase:
                if entry not in node.format:
                    raise RuntimeError("entry not covered in data format")
                word = node.rawEntries[node.format[entry]]
                if word in w2int:
                    node.rawEntries[node.format[entry]] = w2int[word]
                else:
                    node.rawEntries[node.format[entry]] = w2int["<UNK>"]
        return

    def saveModel(self, fileName=""):
        if fileName == "":
            return
        entity = vars(self)
        if fileName.endswith("pklz"):
            output = gzip.open(fileName, 'wb')
        elif fileName.endswith("pkl"):
            output = open(fileName, 'wb')
        else:
            fileName = fileName + ".pkl"
            output = open(fileName, 'wb')

        # dump components
        for componentName in self.component:
            if componentName not in entity:
                raise RuntimeError("object in _savedModelFile doesn't exist")
            self.__saveObjectToFile(entity[componentName], output)

        output.close()
        return

    def __loadObjectFromFile(self, pklFile):
        a = pickle.load(pklFile)
        return a

    def __saveObjectToFile(self, a, output):
        pickle.dump(a, output)
        return

    def argmax(self, x, beamSize=1):
        return sorted(enumerate(x), key=lambda t: -t[1])[:beamSize]


def saveModel(path, pc, encoder, decoder):
    pass
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno != errno.EEXIST:
            print("[WARN]: {} already exist, will be overwritten".format(
                path))
    encoder.saveModel(path + "/encoder.pkl")
    decoder.saveModel(path + "/decoder.pkl")
    pc.save(path + "/params.dynet")
    return


def loadModel(path, pc, encoder, decoder, params):
    pass
    print("[INFO]: Loading model from " + str(path))
    encoder.loadModel(path + "/encoder.pkl")
    decoder.loadModel(path + "/decoder.pkl")
    encoder.buildModel(
        params, pc, encoder.inDim, encoder.hidDim,
        encoder.layers)
    decoder.buildModel(
        params, pc, decoder.inDim, decoder.hidDim,
        decoder.layers)
    pc.populate(path + "/params.dynet")
    print("[INFO]: Loaded")
    return
