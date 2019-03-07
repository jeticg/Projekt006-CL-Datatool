import random
import copy
import progressbar

import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim

import natlang as nl
from natlang._support.logger import logging, initialiseLogger, getCommitHash
from modelBase import ModelBase
__version__ = "0.1b"


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
        self.w2int, self.int2w = ModelBase.buildCoNLLLexicon(
            self, dataset, entry="FORM", lexiconSize=lexiconSize)
        self.t2int, self.int2t = ModelBase.buildCoNLLLexicon(
            self, dataset, entry="UPOS", lexiconSize=lexiconSize)
        for key in ["<SOS>", "<EOS>"]:
            self.t2int[key] = len(self.int2t)
            self.int2t.append(key)
        return

    def convertDataset(self, dataset):
        dataset = copy.deepcopy(dataset)
        ModelBase.convertCoNLL(self, dataset, entry="FORM", w2int=self.w2int)
        ModelBase.convertCoNLL(self, dataset, entry="UPOS", w2int=self.t2int)
        for i in range(len(dataset)):
            sample = dataset[i]
            words = [node.rawEntries[node.format["FORM"]]
                     for node in sample.phrase]
            tags = [node.rawEntries[node.format["UPOS"]]
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


def logSumExp(vec):
    """
    input: vec, variable or tensor of (1, N) shape
    output: max(vec) + log(sum(exp(vec - max(vec))))
    """
    maxScore = torch.max(vec)
    return maxScore + torch.log(torch.sum(torch.exp(vec - maxScore)))


class BiLSTM_CRF(nn.Module):

    def __init__(self, w2int, t2int, inDim, hidDim, layers):
        super(BiLSTM_CRF, self).__init__()
        self.inDim = inDim
        self.hidDim = hidDim
        self.layers = layers
        self.w2int = w2int
        self.t2int = t2int

        self.wordEmbedding = nn.Embedding(len(self.w2int), inDim)
        self.lstm = nn.LSTM(inDim, hidDim // 2,
                            num_layers=layers, bidirectional=True)

        # Maps the output of the LSTM into tag space.
        self.affineLayer = nn.Linear(hidDim, len(self.t2int))

        # Matrix of transition parameters.  Entry i,j is the score of
        # transitioning *to* i *from* j.
        self.transScore = nn.Parameter(
            torch.randn(len(self.t2int), len(self.t2int)))

        # These two statements enforce the constraint that we never transfer
        # to the start tag and we never transfer from the stop tag
        self.transScore.data[self.t2int["<SOS>"], :] = -10000
        self.transScore.data[:, self.t2int["<EOS>"]] = -10000

        self.hiddenRep = self.initHiddenRep()

    def initHiddenRep(self):
        return (torch.randn(2 * self.layers, 1, self.hidDim // 2),
                torch.randn(2 * self.layers, 1, self.hidDim // 2))

    def encode(self, words):
        self.hiddenRep = self.initHiddenRep()
        embeds = self.wordEmbedding(words).view(len(words), 1, -1)
        output, self.hiddenRep = self.lstm(embeds, self.hiddenRep)
        output = output.view(len(words), self.hidDim)
        probs = self.affineLayer(output)
        return probs

    def calcProbsScore(self, probs):
        previous = torch.full((len(self.t2int), ), -10000.)
        previous[self.t2int["<SOS>"]] = 0.

        for prob in probs:
            current = []
            for tag in range(len(self.t2int)):
                current.append(logSumExp(
                    previous + prob[tag] + self.transScore[tag]).view(1))

            previous = torch.cat(current)

        final = logSumExp(previous + self.transScore[self.t2int["<EOS>"]])
        return final

    def calcScore(self, probs, tags):
        score = sum([prob[tags[i]] for i, prob in enumerate(probs)])
        tags = torch.cat([
            torch.tensor([self.t2int["<SOS>"]], dtype=torch.long),
            tags,
            torch.tensor([self.t2int["<EOS>"]], dtype=torch.long)])
        for i in range(len(tags) - 1):
            score += self.transScore[tags[i + 1], tags[i]]
        return score

    def decode(self, probs):
        backpointers = []

        # Initialize the viterbi variables in log space
        init_vvars = torch.full((1, len(self.t2int)), -10000.)
        init_vvars[0][self.t2int["<SOS>"]] = 0

        # forward_var at step i holds the viterbi variables for step i-1
        forward_var = init_vvars
        for prob in probs:
            bptrs_t = []  # holds the backpointers for this step
            viterbivars_t = []  # holds the viterbi variables for this step

            for nextTag in range(len(self.t2int)):
                # nextTag_var[i] holds the viterbi variable for tag i at the
                # previous step, plus the score of transitioning
                # from tag i to nextTag.
                # We don't include the emission scores here because the max
                # does not depend on them (we add them in below)
                nextTag_var = forward_var + self.transScore[nextTag]
                best_tag_id = torch.argmax(nextTag_var)
                bptrs_t.append(best_tag_id)
                viterbivars_t.append(nextTag_var[0][best_tag_id].view(1))
            # Now add in the emission scores, and assign forward_var to the set
            # of viterbi variables we just computed
            forward_var = (torch.cat(viterbivars_t) + prob).view(1, -1)
            backpointers.append(bptrs_t)

        # Transition to "<EOS>"
        terminal_var = forward_var + self.transScore[self.t2int["<EOS>"]]
        best_tag_id = torch.argmax(terminal_var)
        path_score = terminal_var[0][best_tag_id]

        # Follow the back pointers to decode the best path.
        best_path = [best_tag_id]
        for bptrs_t in reversed(backpointers):
            best_tag_id = bptrs_t[best_tag_id]
            best_path.append(best_tag_id)
        # Pop off the start tag (we dont want to return that to the caller)
        start = best_path.pop()
        assert start == self.t2int["<SOS>"]  # Sanity check
        best_path.reverse()
        return path_score, best_path

    def computeSampleLoss(self, sample):
        words, tags = sample
        probs = self.encode(words)
        outputScore = self.calcProbsScore(probs)
        referenceScore = self.calcScore(probs, tags)
        return outputScore - referenceScore

    def computeBatchLoss(self, batchOfSamples):
        loss = []
        for sample in batchOfSamples:
            loss.append(self.computeSampleLoss(sample))
        return sum(loss)

    def forward(self, words):
        probs = self.encode(words)
        score, output = self.decode(probs)
        return score, output


def train(tagger, dataset, epochs, batchSize):
    logger = logging.getLogger('TRAIN')
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
                results[-1] += (i-1,)
        else:
            if len(results) != 0 and len(results[-1]) == 2:
                results[-1] += (i-1,)
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
    config = {
        "epochs": 1,
        "inDim": 256,
        "hidDim": 256,
        "layers": 1,
        "batchSize": 1
    }
    initialiseLogger('tagger.log')
    logger = logging.getLogger('MAIN')
    logger.info("""Natlang toolkit Universal Tagger %s""" % __version__)
    logger.debug("--Commit#: {}".format(getCommitHash()))

    logger.info("Experimenting on CONLL2003 NER Task")
    loader = nl.loader.DataLoader("conll")
    format = nl.format.conll.conll2003
    trainDataset = loader.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.train",
        option={"entryIndex": format})
    valDataset = loader.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.testb",
        option={"entryIndex": format})
    testDataset = loader.load(
        "/Users/jetic/Daten/syntactic-data/CoNLL-2003/eng.testa",
        option={"entryIndex": format})

    trainDataset = [sample for sample in trainDataset
                    if sample is not None and len(sample) != 0][:1000]
    valDataset = [sample for sample in valDataset
                  if sample is not None and len(sample) != 0]
    testDataset = [sample for sample in testDataset
                   if sample is not None and len(sample) != 0]

    logger.info("Initialising Model")
    tagger = Tagger()
    tagger.buildLexicon(trainDataset)
    trainDataset = tagger.convertDataset(trainDataset)
    valDataset = tagger.convertDataset(valDataset)
    testDataset = tagger.convertDataset(testDataset)
    logger.info("Model inDim=%s, hidDim=%s, layser=%s" %
                (config["inDim"], config["hidDim"], config["layers"]))
    tagger.buildModel(inDim=config["inDim"],
                      hidDim=config["hidDim"],
                      layers=config["layers"])
    logger.info("Training with %s epochs, batch size %s" %
                (config["epochs"], config["batchSize"]))
    train(tagger,
          trainDataset,
          epochs=config["epochs"],
          batchSize=config["batchSize"])

    logger.info("Testing with validation dataset")
    resultsVal = test(tagger, valDataset)
    logger.info("Testing with test dataset")
    resultsTest = test(tagger, testDataset)
