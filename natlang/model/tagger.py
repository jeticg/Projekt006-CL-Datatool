from tqdm import tqdm

import torch
import torch.autograd as autograd
import torch.nn as nn
import torch.optim as optim

import natlang as nl
from modelBase import ModelBase


class Tagger(ModelBase):
    def __init__(self, maxTrainLen=50):
        ModelBase.__init__(self)
        self.maxTrainLen = maxTrainLen
        self.w2int = {}
        self.int2w = []
        self.t2int = {}
        self.int2t = []
        self.component = ["maxTrainLen",
                          "inDim", "hidDim", "layers",
                          "w2int", "int2w"]
        self.model = None
        return

    def buildLexicon(self, dataset, lexiconSize=50000):
        self.w2int, self.int2w = ModelBase.buildLexicon(
            self, dataset, entry="FORM", lexiconSize=lexiconSize)
        self.t2int, self.int2t = ModelBase.buildLexicon(
            self, dataset, entry="UPOS", lexiconSize=lexiconSize)
        for key in ["<SOS>", "<EOS>"]:
            self.t2int[key] = len(self.int2t)
            self.int2t.append(key)
        return

    def convertDataset(self, dataset):
        ModelBase.convertDataset(self, dataset, entry="FORM", w2int=self.w2int)
        ModelBase.convertDataset(self, dataset, entry="UPOS", w2int=self.t2int)
        for i in range(len(dataset)):
            sample = dataset[i]
            words = [node.rawEntries[node.format["FORM"]]
                     for node in sample.phrase]
            tags = [node.rawEntries[node.format["UPOS"]]
                    for node in sample.phrase]
            dataset[i] = torch.LongTensor(words), torch.LongTensor(tags)
        return

    def BuildModel(self, inDim, hidDim):
        self.model = BiLSTM_CRF(len(self.int2w), self.t2int, inDim, hidDim)
        return


def to_scalar(var):  # var是Variable,维度是１
    # returns a python float
    return var.view(-1).data.tolist()[0]


def argmax(vec):
    # return the argmax as a python int
    _, idx = torch.max(vec, 1)
    return to_scalar(idx)


def prepare_sequence(seq, to_ix):
    idxs = [to_ix[w] for w in seq]
    tensor = torch.LongTensor(idxs)
    return autograd.Variable(tensor)


# Compute log sum exp in a numerically stable way for the forward algorithm
def log_sum_exp(vec):  # vec是1*5, type是Variable
    max_score = vec[0, argmax(vec)]
    # max_score维度是１，　max_score.view(1,-1)维度是１＊１,
    # max_score.view(1, -1).expand(1, vec.size()[1])的维度是１＊５
    max_score_broadcast = max_score.view(1, -1).expand(1, vec.size()[1])
    # vec.size()维度是1*5
    return max_score + torch.log(
        torch.sum(torch.exp(vec - max_score_broadcast)))
    # 为什么指数之后再求和，而后才log呢


class BiLSTM_CRF(nn.Module):

    def __init__(self, vocab_size, tag_to_ix, embedding_dim, hidden_dim):
        super(BiLSTM_CRF, self).__init__()
        self.embedding_dim = embedding_dim
        self.hidden_dim = hidden_dim
        self.vocab_size = vocab_size
        self.tag_to_ix = tag_to_ix
        self.tagset_size = len(tag_to_ix)

        self.word_embeds = nn.Embedding(vocab_size, embedding_dim)
        self.lstm = nn.LSTM(embedding_dim, hidden_dim // 2,
                            num_layers=1, bidirectional=True)

        # Maps the output of the LSTM into tag space.
        self.hidden2tag = nn.Linear(hidden_dim, self.tagset_size)

        # Matrix of transition parameters.  Entry i,j is the score of
        # transitioning *to* i *from* j.
        self.transitions = nn.Parameter(
            torch.randn(self.tagset_size, self.tagset_size))

        # These two statements enforce the constraint that we never transfer
        # to the start tag and we never transfer from the stop tag
        self.transitions.data[tag_to_ix["<SOS>"], :] = -10000
        self.transitions.data[:, tag_to_ix["<EOS>"]] = -10000

        self.hidden = self.init_hidden()

    def init_hidden(self):
        return (torch.randn(2, 1, self.hidden_dim // 2),
                torch.randn(2, 1, self.hidden_dim // 2))

    def _forward_alg(self, feats):
        # Do the forward algorithm to compute the partition function
        init_alphas = torch.full((1, self.tagset_size), -10000.)
        # "<SOS>" has all of the score.
        init_alphas[0][self.tag_to_ix["<SOS>"]] = 0.

        # Wrap in a variable so that we will get automatic backprop
        forward_var = init_alphas

        # Iterate through the sentence
        for feat in feats:
            alphas_t = []  # The forward tensors at this timestep
            for next_tag in range(self.tagset_size):
                # broadcast the emission score: it is the same regardless of
                # the previous tag
                emit_score = feat[next_tag].view(
                    1, -1).expand(1, self.tagset_size)
                # the ith entry of trans_score is the score of transitioning to
                # next_tag from i
                trans_score = self.transitions[next_tag].view(1, -1)
                # The ith entry of next_tag_var is the value for the
                # edge (i -> next_tag) before we do log-sum-exp
                next_tag_var = forward_var + trans_score + emit_score
                # The forward variable for this tag is log-sum-exp of all the
                # scores.
                alphas_t.append(log_sum_exp(next_tag_var).view(1))
            forward_var = torch.cat(alphas_t).view(1, -1)
        terminal_var = forward_var + self.transitions[self.tag_to_ix["<EOS>"]]
        alpha = log_sum_exp(terminal_var)
        return alpha

    def _get_lstm_features(self, sentence):
        self.hidden = self.init_hidden()
        embeds = self.word_embeds(sentence).view(len(sentence), 1, -1)
        lstm_out, self.hidden = self.lstm(embeds, self.hidden)
        lstm_out = lstm_out.view(len(sentence), self.hidden_dim)
        lstm_feats = self.hidden2tag(lstm_out)
        return lstm_feats

    def _score_sentence(self, feats, tags):
        # Gives the score of a provided tag sequence
        score = torch.zeros(1)
        tags = torch.cat([torch.tensor([self.tag_to_ix["<SOS>"]], dtype=torch.long), tags])
        for i, feat in enumerate(feats):
            score = score + \
                self.transitions[tags[i + 1], tags[i]] + feat[tags[i + 1]]
        score = score + self.transitions[self.tag_to_ix["<EOS>"], tags[-1]]
        return score

    def _viterbi_decode(self, feats):
        backpointers = []

        # Initialize the viterbi variables in log space
        init_vvars = torch.full((1, self.tagset_size), -10000.)
        init_vvars[0][self.tag_to_ix["<SOS>"]] = 0

        # forward_var at step i holds the viterbi variables for step i-1
        forward_var = init_vvars
        for feat in feats:
            bptrs_t = []  # holds the backpointers for this step
            viterbivars_t = []  # holds the viterbi variables for this step

            for next_tag in range(self.tagset_size):
                # next_tag_var[i] holds the viterbi variable for tag i at the
                # previous step, plus the score of transitioning
                # from tag i to next_tag.
                # We don't include the emission scores here because the max
                # does not depend on them (we add them in below)
                next_tag_var = forward_var + self.transitions[next_tag]
                best_tag_id = argmax(next_tag_var)
                bptrs_t.append(best_tag_id)
                viterbivars_t.append(next_tag_var[0][best_tag_id].view(1))
            # Now add in the emission scores, and assign forward_var to the set
            # of viterbi variables we just computed
            forward_var = (torch.cat(viterbivars_t) + feat).view(1, -1)
            backpointers.append(bptrs_t)

        # Transition to "<EOS>"
        terminal_var = forward_var + self.transitions[self.tag_to_ix["<EOS>"]]
        best_tag_id = argmax(terminal_var)
        path_score = terminal_var[0][best_tag_id]

        # Follow the back pointers to decode the best path.
        best_path = [best_tag_id]
        for bptrs_t in reversed(backpointers):
            best_tag_id = bptrs_t[best_tag_id]
            best_path.append(best_tag_id)
        # Pop off the start tag (we dont want to return that to the caller)
        start = best_path.pop()
        assert start == self.tag_to_ix["<SOS>"]  # Sanity check
        best_path.reverse()
        return path_score, best_path

    def neg_log_likelihood(self, sentence, tags):
        feats = self._get_lstm_features(sentence)
        forward_score = self._forward_alg(feats)
        gold_score = self._score_sentence(feats, tags)
        return forward_score - gold_score

    def forward(self, sentence):  # dont confuse this with _forward_alg above.
        # Get the emission scores from the BiLSTM
        lstm_feats = self._get_lstm_features(sentence)

        # Find the best path, given the features.
        score, tag_seq = self._viterbi_decode(lstm_feats)
        return score, tag_seq

def train(tagger, trainDataset, epochs):
    model = tagger.model
    optimizer = optim.SGD(model.parameters(), lr=0.01, weight_decay=1e-4)

    # Make sure prepare_sequence from earlier in the LSTM section is loaded
    for epoch in range(epochs):
        print("Training epoch %s" % (epoch))
        for words, tags in tqdm(trainDataset):
            model.zero_grad()
            neg_log_likelihood = model.neg_log_likelihood(words, tags)
            neg_log_likelihood.backward()
            optimizer.step()


def test(tagger, testDataset):
    with torch.no_grad():
        results = []
        for words, _ in testDataset:
            result.append(tagger.model(words)[1])
    return results


if __name__ == "__main__":
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

    tagger = Tagger()
    tagger.buildLexicon(trainDataset)
    tagger.convertDataset(trainDataset)
    tagger.convertDataset(testDataset)
    tagger.BuildModel(inDim=256, hidDim=256)
    train(tagger, trainDataset, epochs=5)
    results = test(tagger, testDataset)
