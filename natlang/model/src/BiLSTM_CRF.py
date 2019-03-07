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
