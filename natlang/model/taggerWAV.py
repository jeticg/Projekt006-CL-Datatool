# -*- coding: utf-8 -*-
# Python version: 2/3
#
# NER Tagger
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
from natlang._support.logger import logging, initialiseLogger, getCommitHash
from natlang.model.modelBase import ModelBase
from natlang.model.src.BiLSTM_CRF import Model as BiLSTM_CRF
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
                          "inDim", "hidDim", "layers"]
        self.model = None
        return

    def buildLexicon(self, dataset, lexiconSize=50000):
        self.w2int, self.int2w = ModelBase.buildCoNLLLexicon(
            self, dataset, entry="FORM", lexiconSize=lexiconSize)
        self.t2int, self.int2t = ModelBase.buildCoNLLLexicon(
            self, dataset, entry="NER", lexiconSize=lexiconSize)
        for key in ["<SOS>", "<EOS>"]:
            self.t2int[key] = len(self.int2t)
            self.int2t.append(key)
        return

    def convertDataset(self, dataset):
        dataset = copy.deepcopy(dataset)
        ModelBase.convertCoNLL(self, dataset, entry="FORM", w2int=self.w2int)
        ModelBase.convertCoNLL(self, dataset, entry="NER", w2int=self.t2int)
        for i in range(len(dataset)):
            sample = dataset[i]
            words = [node.rawEntries[node.format["FORM"]]
                     for node in sample.phrase]
            tags = [node.rawEntries[node.format["NER"]]
                    for node in sample.phrase]
            dataset[i] = torch.LongTensor(words), torch.LongTensor(tags)
        return dataset

    def buildModel(self, inDim, hidDim, layers):
        self.inDim = inDim
        self.hidDim = hidDim
        self.layers = layers
        self.model = BiLSTM_CRF(self.w2int, self.t2int, inDim, hidDim, layers)
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
    scores = evaluatorNER(output, reference)
    for key in scores:
        logger.info("  %s = %s" % (key, scores[key]))
    return output


def getBIOSpans(tags):
    tags = tags + ['O']
    results = []
    previous = 'O'
    for i in range(len(tags)):
        if tags[i] == previous:
            continue
        if previous[0] == 'B' and tags[i][0] == 'i' and\
                tags[i][1:] == previous[1:]:
            previous = tags[i]
            continue
        elif tags[i] == 'O':
            if len(results) != 0 and len(results[-1]) == 2:
                results[-1] += (i - 1,)
        else:
            if len(results) != 0 and len(results[-1]) == 2:
                results[-1] += (i - 1,)
            results.append((tags[i][2:], i, ))
        previous = tags[i]
    return results


def evaluatorNER(output, reference):
    correct = 0.0
    totalRef = 0.0
    totalOut = 0.0
    for tags, refTags in zip(output, reference):
        out = getBIOSpans(tags)
        ref = getBIOSpans(refTags)
        correct += len([item for item in out if item in ref])
        totalOut += len(out)
        totalRef += len(ref)
    precision = 1. * correct / totalOut
    recall = 1. * correct / totalRef
    F1 = 2. * precision * recall / (precision + recall)
    return {"Precision": precision,
            "Recall": recall,
            "F1": F1}


if __name__ == "__main__":
    progID = """Natlang toolkit Universal Tagger %s""" % __version__
    config = {
        "epochs": 5,
        "inDim": 256,
        "hidDim": 256,
        "layers": 1,
        "batchSize": 1
    }
    initialiseLogger('taggerNER.log')
    logger = logging.getLogger('MAIN')
    config = processConfig(progID, config)
    logger.info(progID)
    logger.debug("--Commit#: {}".format(getCommitHash()))

    logger.info("Experimenting on CONLL2003 NER Task")
    trainDataset = nl.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.train",
        format=nl.format.conll,
        option={"entryIndex": nl.format.conll.conll2003})
    valDataset = nl.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.testb",
        format=nl.format.conll,
        option={"entryIndex": nl.format.conll.conll2003})
    testDataset = nl.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.testa",
        format=nl.format.conll,
        option={"entryIndex": nl.format.conll.conll2003})

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
