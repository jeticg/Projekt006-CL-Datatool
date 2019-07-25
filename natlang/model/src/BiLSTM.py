import random
import copy
import progressbar

import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim

import natlang as nl


def logSumExp(vec):
    """
    input: vec, variable or tensor of (1, N) shape
    output: max(vec) + log(sum(exp(vec - max(vec))))
    """
    maxScore = torch.max(vec)
    return maxScore + torch.log(torch.sum(torch.exp(vec - maxScore)))


class Model(nn.Module):

    def __init__(self, w2int, t2int, inDim, hidDim, layers):
        super(Model, self).__init__()
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

        self.hiddenRep = self.initHiddenRep()
        self.lossFunction = nn.NLLLoss()

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

    def decode(self, probs):
        result = []
        score = []
        for prob in probs:
            result.append(torch.argmax(prob))
            score.append(prob[result[-1]])
        return score, result

    def computeSampleLoss(self, sample):
        words, tags = sample
        probs = self.encode(words)
        probs = torch.nn.functional.log_softmax(probs, dim=1)
        loss = self.lossFunction(probs, tags)
        return loss

    def computeBatchLoss(self, batchOfSamples):
        loss = []
        for sample in batchOfSamples:
            loss.append(self.computeSampleLoss(sample))
        return sum(loss)

    def forward(self, words):
        probs = self.encode(words)
        score, output = self.decode(probs)
        return score, output
