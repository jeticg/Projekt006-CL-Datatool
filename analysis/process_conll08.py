from support.fileIO import loadSemFrame
from bisect import bisect_left
from collections import namedtuple


def read_sentences(file):
    lines = []
    for line in file:
        if line == '\n':
            yield lines
            lines.clear()
        else:
            lines.append(line.strip().split('\t'))


class TreeNode:
    def __init__(self, info, children=None):
        self.info = info
        if children is None:
            self.children = []
        else:
            self.children = children

    def __repr__(self):
        return f'TreeNode({self.info})'


FORM_OFFSET = 1
PPOS_OFFSET = 7
HEAD_OFFSET = 8
DEPREL_OFFSET = 9
PRED_OFFSET = 10
ARGS_OFFSET = 11


def is_pred(word):
    return word[PRED_OFFSET] != '_'


ArgData = namedtuple('ArgData', ['pred_node', 'pred_name', 'args_dict'])


def parse_sentence(sentence):
    """

    :param sentence:
    :return:
        root: the root node of the tree
        args_data: [(predicate node, predicate name, {arg name: arg node})]
        for predicates in the order they appear in the sentence
    """
    root = None
    nodes = []
    for word in sentence:
        nodes.append(TreeNode(word[FORM_OFFSET:PPOS_OFFSET + 1]))

    for i, word in enumerate(sentence):
        head_idx, rel = int(word[HEAD_OFFSET]), word[DEPREL_OFFSET]
        if head_idx > 0:
            nodes[head_idx - 1].children.append((nodes[i], rel))
        else:
            root = nodes[i]

    preds = []
    pred_names = []
    for i, word in enumerate(sentence):
        if is_pred(word):
            preds.append(nodes[i])
            pred_names.append(word[PRED_OFFSET])

    args_data = [(x, y, {}) for x, y in zip(preds, pred_names)]
    for i, word in enumerate(sentence):
        args = word[ARGS_OFFSET:]
        for j, arg in enumerate(args):
            if arg != '_':
                args_data[j][-1][arg] = nodes[i]

    return root, args_data


def load_frames():
    pb_frames = loadSemFrame('data/pb_frames/*.xml')
    return pb_frames


def process_frames(frames):
    l = [x[0] for x in frames]
    l.sort()
    return l


def verify_idx(names, pred_name):
    idx = bisect_left(names, pred_name)
    return idx < len(names) and names[idx] == pred_name


def filter_args_data(pb_names, args_data):
    pb_data = []
    for data in args_data:
        pred_name = data[1]
        if verify_idx(pb_names, pred_name):
            pb_data.append(data)

    return pb_data


if __name__ == '__main__':
    with open('data/conll08st/data/train/train.closed') as file:
        sentences = read_sentences(file)
        pb_frames = load_frames()
        pb_names = process_frames(pb_frames)

        for sentence in sentences:
            root, args_data = parse_sentence(sentence)
            pb_data = filter_args_data(pb_names, args_data)
            break
