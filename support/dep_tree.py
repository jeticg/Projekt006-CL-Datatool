# -*- coding: utf-8 -*-
# Python version: 3.6+
#
# Dependency Tree class
# Simon Fraser University
# Ruoyi Wang
#
# This module contains functions and classes necessary for loading
# penn treebank format sentences with dependency information. 2 examples are
# provided in sampleDepTree.txt
#

from support.fileIO import loadSemFrame
from bisect import bisect_left

FORM_OFFSET = 1
PPOS_OFFSET = 7
HEAD_OFFSET = 8
DEPREL_OFFSET = 9
PRED_OFFSET = 10
ARGS_OFFSET = 11


class TreeNode:
    def __init__(self, parent=None):
        # info = (POS, FORM)
        self.info = None
        self.parent = parent
        self.rel = None
        # frame is the predicate name
        self.frame = None
        # args: {arg name: arg node}
        self.args = None

        self.next_sib = None
        # first left child
        self.flc = None
        # first right child
        self.frc = None

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

    def __repr__(self):
        return f'TreeNode({self.info})'


def export_to_vec(node):
    """export the tree at node to a vec of FORMs representing the original sentence"""
    words = []
    for n in inorder_traversal(node):
        words.append(n.info[1])
    return words


def export_to_table(node):
    """export the tree to a table with similar structure of the original table"""
    # reconstruct args_data
    args_data = []
    for n in inorder_traversal(node):
        if n.frame is not None:
            args_data.append((n, n.frame, n.args))

    table = []
    indices = {}
    for i, n in enumerate(inorder_traversal(node)):
        table.append([i + 1, n.info[1], n.info[0]])
        indices[n] = i

    for n, i in indices.items():
        if n.parent is None:
            table[i].extend([0, 'ROOT'])
        else:
            table[i].extend([indices[n.parent] + 1, n.rel])

    for x in table:
        x.append('_')
    for arg_data in args_data:
        pred_node, pred_name, args_dict = arg_data
        table[indices[pred_node]][-1] = pred_name

    for arg_data in args_data:
        for x in table:
            x.append('_')
        pred_node, pred_name, args_dict = arg_data
        for arg_name, arg_node in args_dict.items():
            table[indices[arg_node]][-1] = arg_name

    return table


def inorder_traversal(node):
    if node.flc is not None:
        yield from inorder_traversal(node.flc)
    yield node
    if node.frc is not None:
        yield from inorder_traversal(node.frc)
    if node.next_sib is not None:
        yield from inorder_traversal(node.next_sib)


def is_pred(word):
    return word[PRED_OFFSET] != '_'


def read_sentences(file):
    lines = []
    for line in file:
        if line == '\n':
            yield lines
            lines.clear()
        else:
            lines.append(line.strip().split('\t'))
    if len(lines):
        yield lines


def parse_sentence(pb_names, sentence):
    """construct the dependecy tree and return the root"""
    nodes = []
    # construct a node for each word
    for word in sentence:
        node = TreeNode()
        node.info = word[PPOS_OFFSET], word[FORM_OFFSET]
        nodes.append(node)

    # link the nodes into a tree
    root = None
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

    # extract predicate info
    preds = []
    pred_names = []
    for i, word in enumerate(sentence):
        if is_pred(word):
            pred_name = word[PRED_OFFSET]
            preds.append(nodes[i])
            pred_names.append(pred_name)

    # link predicate info to the nodes
    args_data = [(x, y, {}) for x, y in zip(preds, pred_names)]
    for i, word in enumerate(sentence):
        args = word[ARGS_OFFSET:]
        for j, arg in enumerate(args):
            if arg != '_':
                args_data[j][-1][arg] = nodes[i]

    # filter irrelevant predicates
    pb_data = filter_args_data(pb_names, args_data)

    # insert predicates info into the tree nodes
    for node, name, d in pb_data:
        node.frame = name
        node.args = d
    return root


def load_frames(frames_path):
    """load frame info"""
    pb_frames = loadSemFrame(f'{frames_path}/*.xml')
    return pb_frames


def process_frames(frames):
    """extract only the frame name and sort"""
    l = [x[0] for x in frames]
    l.sort()
    return l


def _verify_name(names, pred_name):
    """verify the pred name is in the SORTED list of pred names"""
    idx = bisect_left(names, pred_name)
    return idx < len(names) and names[idx] == pred_name


def filter_args_data(pb_names, args_data):
    """remove args data that are not in TreeBank"""
    pb_data = []
    for data in args_data:
        pred_name = data[1]
        if _verify_name(pb_names, pred_name):
            pb_data.append(data)

    return pb_data


def parse_dep_tree(frames_path, file):
    """
    main entry point
    read dependency tree file and construct a forest
    each tree represents a sentence
    trees appear in the forest in the order of the original sentences
    """
    sentences = read_sentences(file)
    pb_frames = load_frames(frames_path)
    pb_names = process_frames(pb_frames)

    forest = []
    for sentence in sentences:
        root = parse_sentence(pb_names, sentence)
        forest.append(root)
    return forest


if __name__ == '__main__':
    with open('support/sampleDepTree.txt') as file:
        forest = parse_dep_tree('data/pb_frames', file)
    export_to_table(forest[1])
