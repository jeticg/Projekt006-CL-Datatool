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
    def __init__(self, POS, form, parent=None, rel=None, next_sib=None, flc=None, frc=None):
        # info = (POS, FORM)
        self.info = POS, form

        self.parent = parent
        self.rel = rel
        self.next_sib = next_sib
        # first left child
        self.flc = flc
        # first right child
        self.frc = frc

    def last_left_child(self):
        if self.flc is None:
            return None
        node = self.flc
        while node.next_sib is not None:
            node = node.next_sib
        return node

    def last_right_child(self):
        if self.frc is None:
            return None
        node = self.frc
        while node.next_sib is not None:
            node = node.next_sib
        return node

    def append_left_child(self, node, rel):
        node.parent = self
        node.rel = rel
        llc = self.last_left_child()
        if llc is None:
            self.flc = node
        else:
            llc.next_sib = node

    def append_right_child(self, node, rel):
        node.parent = self
        node.rel = rel
        lrc = self.last_right_child()
        if lrc is None:
            self.frc = node
        else:
            lrc.next_sib = node

    def export_to_vec(self):
        words = []
        for node in inorder_traversal(self):
            words.append(node.info[1])
        return words

    def export_to_table(self):
        pass

    def __repr__(self):
        return f'TreeNode({self.info})'


def inorder_traversal(node):
    if node.flc is not None:
        yield from inorder_traversal(node.flc)
    yield node
    if node.frc is not None:
        yield from inorder_traversal(node.frc)
    if node.next_sib is not None:
        yield from inorder_traversal(node.next_sib)


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
    :return:
        root: the root node of the tree
        args_data: [(predicate node, predicate name, {arg name: arg node})]
        for predicates in the order they appear in the sentence
    """
    root = None
    nodes = []
    for word in sentence:
        nodes.append(TreeNode(word[PPOS_OFFSET], word[FORM_OFFSET]))

    for i, word in enumerate(sentence):
        head_idx, rel = int(word[HEAD_OFFSET]), word[DEPREL_OFFSET]
        if head_idx > 0:
            parent_idx = head_idx - 1
            if parent_idx > i:
                nodes[parent_idx].append_left_child(nodes[i], rel)
            else:
                nodes[parent_idx].append_right_child(nodes[i], rel)
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
