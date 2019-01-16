# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Sequence Labeller: Bidirectional LSTM with Softmax Layer
# Simon Fraser University
# Jetic Gu
#
#
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import tqdm

import natlang as nl
torch.manual_seed(1)


def argmax(vector):
    _, index = torch.max(vector, 1)
    return index


def convert2Index(seq, to_ix):
    idxs = [to_ix[w] for w in seq]
    return torch.tensor(idxs, dtype=torch.long)


def extractData(files):
    def separateTag(sequence):
        return ([entry[1] for entry in sequence],
                [entry[0] for entry in sequence])
    loader = nl.loader.DataLoader("tree")
    data = loader.load(files)
    data = [separateTag(entry.phrase) for entry in data]
    return data


def batcher(batch):
    result = []
    for sentence in batch:
        result.append(convert2Index(sentence))
    return torch.tensor(result)


trainData = extractData("~/Daten/syntactic-data/Penn_Treebank/train.tree.en")
valData = extractData("~/Daten/syntactic-data/Penn_Treebank/test1.tree.en")
testData = extractData("~/Daten/syntactic-data/Penn_Treebank/test2.tree.en")

w2int = {}
t2int = {}
int2t = []
for sentence, tag in trainData:
    for w in sentence:
        if w not in w2int:
            w2int[w] = len(w2int)
    for t in tag:
        if t not in t2int:
            t2int[t] = len(t2int)
            int2t.append(t)

# These will usually be more like 32 or 64 dimensional.
# We will keep them small, so we can see how the weights change as we train.
EMBEDDING_DIM = 300
HIDDEN_DIM = 300


class Tagger(nn.Module):
    def __init__(self, inDim, hidDim, layers, vocab_size, tagset_size):
        super(Tagger, self).__init__()
        self.hidDim = hidDim
        self.layers = layers

        self.word_embeddings = nn.Embedding(vocab_size, inDim)

        # The LSTM takes word embeddings as inputs, and outputs hidden states
        # with dimensionality hidDim.
        self.lstm = nn.LSTM(inDim, hidDim,
                            num_layers=self.layers,
                            bidirectional=True)

        # The linear layer that maps from hidden state space to tag space
        self.hidden2tag = nn.Linear(hidDim * self.layers, tagset_size)
        self.hidden = self.init_hidden()
        self.lossFunc = nn.NLLLoss()
        return

    def init_hidden(self):
        return (torch.zeros(2 * self.layers, 1, self.hidDim),
                torch.zeros(2 * self.layers, 1, self.hidDim))

    def forward(self, input):
        embeds = self.word_embeddings(input)
        lstm_out, self.hidden = self.lstm(
            embeds.view(len(input), 1, -1), self.hidden)
        output = self.hidden2tag(lstm_out.view(len(input), -1))
        prediction = F.log_softmax(output, dim=1)
        return prediction

    def computeLoss(self, input, reference):
        self.zero_grad()
        self.hidden = self.init_hidden()
        prediction = self(convert2Index(input, w2int))
        return self.lossFunc(prediction,
                             convert2Index(reference, t2int))


model = Tagger(EMBEDDING_DIM, HIDDEN_DIM, 2, len(w2int), len(t2int))
optimizer = optim.SGD(model.parameters(), lr=0.1)

# See what the scores are before training
# Note that element i,j of the output is the score for tag j for word i.
# Here we don't need to train, so the code is wrapped in torch.no_grad()
with torch.no_grad():
    inputs = convert2Index(trainData[0][0], w2int)
    prediction = model(inputs)
    print(prediction)

for epoch in range(20):
    print(f"Starting epoch {epoch}")
    for sentence, tags in tqdm.tqdm(trainData):
        loss = model.computeLoss(sentence, tags)
        loss.backward()
        optimizer.step()

# See what the scores are after training
with torch.no_grad():
    inputs = convert2Index(trainData[0][0], w2int)
    prediction = argmax(model(inputs))
    prediction = [int2t[index.item()] for index in prediction]
    print(prediction)
