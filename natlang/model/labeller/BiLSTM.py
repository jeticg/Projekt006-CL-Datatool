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

torch.manual_seed(1)


def argmax(vector):
    _, index = torch.max(vector, 1)
    return index


def convert2Index(seq, to_ix):
    idxs = [to_ix[w] for w in seq]
    return torch.tensor(idxs, dtype=torch.long)


training_data = [
    ("The dog ate the apple".split(), ["DET", "NN", "V", "DET", "NN"]),
    ("Everybody read that book".split(), ["NN", "V", "DET", "NN"])
]
word_to_ix = {}
for sent, tags in training_data:
    for word in sent:
        if word not in word_to_ix:
            word_to_ix[word] = len(word_to_ix)
print(word_to_ix)
tag_to_ix = {"DET": 0, "NN": 1, "V": 2}
ix_to_tag = ["DET", "NN", "V"]

# These will usually be more like 32 or 64 dimensional.
# We will keep them small, so we can see how the weights change as we train.
EMBEDDING_DIM = 6
HIDDEN_DIM = 6


class Tagger(nn.Module):
    def __init__(self, inDim, hidDim, vocab_size, tagset_size):
        super(Tagger, self).__init__()
        self.hidDim = hidDim

        self.word_embeddings = nn.Embedding(vocab_size, inDim)

        # The LSTM takes word embeddings as inputs, and outputs hidden states
        # with dimensionality hidDim.
        self.lstm = nn.LSTM(inDim, hidDim)

        # The linear layer that maps from hidden state space to tag space
        self.hidden2tag = nn.Linear(hidDim, tagset_size)
        self.hidden = self.init_hidden()
        self.lossFunc = nn.NLLLoss()
        return

    def init_hidden(self):
        return (torch.zeros(1, 1, self.hidDim),
                torch.zeros(1, 1, self.hidDim))

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
        prediction = self(convert2Index(input, word_to_ix))
        return self.lossFunc(prediction,
                             convert2Index(reference, tag_to_ix))


model = Tagger(EMBEDDING_DIM, HIDDEN_DIM, len(word_to_ix), len(tag_to_ix))
optimizer = optim.SGD(model.parameters(), lr=0.1)

# See what the scores are before training
# Note that element i,j of the output is the score for tag j for word i.
# Here we don't need to train, so the code is wrapped in torch.no_grad()
with torch.no_grad():
    inputs = convert2Index(training_data[0][0], word_to_ix)
    prediction = model(inputs)
    print(prediction)

for epoch in range(300):
    for sentence, tags in training_data:
        loss = model.computeLoss(sentence, tags)
        loss.backward()
        optimizer.step()

# See what the scores are after training
with torch.no_grad():
    inputs = convert2Index(training_data[0][0], word_to_ix)
    prediction = argmax(model(inputs))
    prediction = [ix_to_tag[index.item()] for index in prediction]
    print(prediction)
