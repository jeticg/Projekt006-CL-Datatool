# -*- coding: utf-8 -*-
# Python version: 2/3
#
# POS Tagger
# Simon Fraser University
# Jetic Gu
#
import random
import copy
import progressbar

import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim

import natlang as nl
from natlang._support.argparser import processConfig
from natlang._support.logger import logging, initialiseLogger, getCommitHash
from natlang.format.conll import Node as ConllNode
from natlang.format.tree import Node as TreeNode
from natlang.model.modelBase import ModelBase
from natlang.model.src.BiLSTM import Model as BiLSTM
__version__ = "0.1b1"


class Tagger(ModelBase):
    def __init__(self, maxTrainLen=50):
        ModelBase.__init__(self)
        self.maxTrainLen = maxTrainLen
        self.w2int = {}
        self.int2w = []
        self.t2int = {}
        self.int2t = []
        self.inDim = self.hidDim = self.layers = None
        self.component = ["maxTrainLen",
                          "inDim", "hidDim", "layers",
                          "w2int", "int2w",
                          "t2int", "int2t"]
        self.model = None
        return

    def buildLexicon(self, dataset, lexiconSize=50000):
        wordSet = []
        tagSet = []
        for i in range(len(dataset)):
            sample = dataset[i]
            if isinstance(sample, ConllNode):
                words = [node.rawEntries[node.format["FORM"]]
                         for node in sample.phrase]
                tags = [node.rawEntries[node.format["UPOS"]]
                        for node in sample.phrase]
            elif isinstance(sample, TreeNode):
                words = [w for t, w in sample.phrase]
                tags = [t for t, w in sample.phrase]
            else:
                raise TypeError("Unrecognised data type in dataset")
            wordSet.append(words)
            tagSet.append(tags)
        self.w2int, self.int2w = self.buildLexiconOnWords(wordSet, lexiconSize)
        self.t2int, self.int2t = self.buildLexiconOnWords(tagSet, lexiconSize)
        return

    def convertDataset(self, dataset):
        dataset = copy.deepcopy(dataset)
        for i in range(len(dataset)):
            sample = dataset[i]
            if isinstance(sample, ConllNode):
                words = [node.rawEntries[node.format["FORM"]]
                         for node in sample.phrase]
                tags = [node.rawEntries[node.format["UPOS"]]
                        for node in sample.phrase]
            elif isinstance(sample, TreeNode):
                words = [w for t, w in sample.phrase]
                tags = [t for t, w in sample.phrase]
            else:
                print(type(sample))
                raise TypeError("Unrecognised data type in dataset")
            for j in range(len(words)):
                words[j] = self.w2int["<UNK>"] if words[j] not in self.w2int\
                    else self.w2int[words[j]]
                tags[j] = self.t2int["<UNK>"] if tags[j] not in self.t2int\
                    else self.t2int[tags[j]]
            dataset[i] = torch.LongTensor(words), torch.LongTensor(tags)
        return dataset

    def buildModel(self, inDim, hidDim, layers):
        self.inDim = inDim
        self.hidDim = hidDim
        self.layers = layers
        self.model = BiLSTM(self.w2int, self.t2int, inDim, hidDim, layers)
        return

    def _buildModelFromSaved(self):
        self.buildModel(self.inDim, self.hidDim, self.layers)

    def sent2indices(self, sent):
        result = []
        for word in sent:
            if word in self.w2int:
                result.append(self.w2int[word])
            else:
                result.append(self.w2int["<UNK>"])
        return torch.LongTensor(result)

    def __call__(self, input):
        if isinstance(input, str):
            sent = input.lower().strip().split()
        elif isinstance(input, list):
            sent = input
        else:
            raise ValueError("Invalid tagger input")
        indices = self.sent2indices(sent)
        result = self.model(indices)
        return sent, [self.int2t[tag] for tag in result[1]]


def train(tagger, dataset, epochs, batchSize,
          inDim=256, hidDim=256, layers=1, rebuild=True):
    logger = logging.getLogger('TRAIN')
    if rebuild is True:
        tagger.buildLexicon(dataset)
        logger.info("Model inDim=%s, hidDim=%s, layser=%s" %
                    (config["inDim"], config["hidDim"], config["layers"]))
        tagger.buildModel(inDim=inDim,
                          hidDim=hidDim,
                          layers=layers)
    dataset = [sample for sample in dataset
               if sample is not None and len(sample) != 0]
    dataset = tagger.convertDataset(dataset)
    logger.info("Training with %s epochs, batch size %s" %
                (config["epochs"], config["batchSize"]))
    model = tagger.model
    optimizer = optim.SGD(model.parameters(), lr=0.01, weight_decay=1e-4)

    trainOrder =\
        [x * batchSize for x in range(len(dataset) // batchSize + 1)]
    widgets = [progressbar.Bar('>'), ' ', progressbar.ETA(),
               progressbar.FormatLabel(
               '; Total: %(value)d batches (in: %(elapsed)s)')]
    trainProgressBar =\
        progressbar.ProgressBar(widgets=widgets,
                                maxval=epochs * len(trainOrder)).start()

    # prepare batching
    if batchSize != 1:
        dataset.sort(key=lambda sample: -len(sample[0]))
        totalBatches = 0
        for epoch in range(epochs):
            logger.info("Training epoch %s" % (epoch))
            random.shuffle(trainOrder)
            for i, index in enumerate(trainOrder, start=1):
                batch = dataset[index:index + batchSize]
                if len(batch) == 0:
                    continue
                model.zero_grad()
                loss = model.computeBatchLoss(batch)
                loss.backward()
                optimizer.step()
                totalBatches += 1
                trainProgressBar.update(totalBatches)
    else:
        totalBatches = 0
        for epoch in range(epochs):
            logger.info("Training epoch %s" % (epoch))
            for sample in dataset:
                model.zero_grad()
                loss = model.computeSampleLoss(sample)
                loss.backward()
                optimizer.step()
                totalBatches += 1
                trainProgressBar.update(totalBatches)

    trainProgressBar.finish()
    return


def test(tagger, testDataset):
    testDataset = [sample for sample in testDataset
                   if sample is not None and len(sample) != 0]
    testDataset = tagger.convertDataset(testDataset)
    logger = logging.getLogger('EVALUATOR')
    correct = 0
    total = 0
    output = []
    reference = []
    with torch.no_grad():
        for words, refTags in testDataset:
            tags = tagger.model(words)[1]
            output.append([tagger.int2t[tag] for tag in tags])
            reference.append([tagger.int2t[tag] for tag in refTags])
            for t, ref in zip(tags, refTags):
                total += 1
                if t == ref:
                    correct += 1
    logger.info("  Accuracy = %s" % (correct * 1.0 / total,))
    return output


if __name__ == "__main__":
    progID = """Natlang toolkit Universal Tagger %s""" % __version__
    config = {
        "epochs": 5,
        "inDim": 256,
        "hidDim": 256,
        "layers": 1,
        "batchSize": 128
    }
    initialiseLogger('taggerPOS.log')
    logger = logging.getLogger('MAIN')
    config = processConfig(progID, config)
    logger.info(progID)
    logger.debug("--Commit#: {}".format(getCommitHash()))

    logger.info("Experimenting on CONLL2003 UPOS Task")
    trainDataset = nl.load(
        "~/Daten/syntactic-data/Penn_Treebank/train.tree.en",
        format=nl.format.tree)
    valDataset = nl.load(
        "~/Daten/syntactic-data/Penn_Treebank/test1.tree.en",
        format=nl.format.tree)
    testDataset = nl.load(
        "~/Daten/syntactic-data/Penn_Treebank/test2.tree.en",
        format=nl.format.tree)

    logger.info("Initialising Model")
    tagger = Tagger()

    train(tagger,
          trainDataset,
          epochs=config["epochs"],
          batchSize=config["batchSize"],
          inDim=config["inDim"],
          hidDim=config["hidDim"],
          layers=config["layers"],
          rebuild=True)

    logger.info("Testing with validation dataset")
    resultsVal = test(tagger, valDataset)
    logger.info("Testing with test dataset")
    resultsTest = test(tagger, testDataset)
