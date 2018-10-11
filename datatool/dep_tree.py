# -*- coding: utf-8 -*-
# Python version: 2.7
#
# Dependency Tree class
# Simon Fraser University
# Ruoyi Wang
#
# This module contains is used for loading
# penn treebank format sentences with dependency information
# 2 examples are provided in sampleDepTree.txt
#

import os
import sys
import inspect
from bisect import bisect_left
import itertools
import copy

currentdir = \
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from loader.SemanticFrame import load as loadSemFrame

FORM_OFFSET = 1
PPOS_OFFSET = 7
HEAD_OFFSET = 8
DEPREL_OFFSET = 9
PRED_OFFSET = 10
ARGS_OFFSET = 11


class TreeNode:
    def __init__(self, parent=None):
        # value = (POS, FORM)
        self.value = None
        self.parent = parent
        # dependency relationship with parent
        self.rel = None
        # frame is the predicate name
        self.frame = None
        # args: {arg name: arg node}
        self.args = None

        # next sibling
        self.next_sib = None
        # first left child
        self.flc = None
        # first right child
        self.frc = None

        self.phrase = []

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
        return 'TreeNode({})'.format(self.value)

    def calcPhrase(self, force=False):  # todo: figure out the desired result
        raise NotImplementedError


def export_to_vec(node):
    """
    export the tree at node to a vec of (POS, FORM) representing the original
    sentence
    """
    words = []
    for n in inorder_traversal(node):
        words.append(n.info)
    return words


def export_to_table(node):
    """
    export the tree to a table
    columns:
    0: id. starting from 1
    1: FORM
    2: POS
    3: parent id
    4: dependency relationship
    5: predicate name
    6+: arguments info
    """
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
        for n in inorder_traversal(node.flc):
            yield n
    yield node
    if node.frc is not None:
        for n in inorder_traversal(node.frc):
            yield n
    if node.next_sib is not None:
        for n in inorder_traversal(node.next_sib):
            yield n


def _is_pred(word):
    return word[PRED_OFFSET] != '_'


def read_sentences(f):
    """split the file into tables, each representing a sentence"""
    lines = []
    for line in f:
        if line == '\n':
            yield lines
            del lines[:]
        else:
            lines.append(line.strip().split('\t'))
    if len(lines):
        yield lines


def _parse_sentence(pb_names, sentence):
    """construct the dependency tree and return the root"""
    nodes = []
    # construct a node for each word
    for word in sentence:
        node = TreeNode()
        node.value = word[PPOS_OFFSET], word[FORM_OFFSET]
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
        if _is_pred(word):
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
    pb_data = _filter_args_data(pb_names, args_data)

    # insert predicates info into the tree nodes
    for node, name, d in pb_data:
        node.frame = name
        node.args = d
    return root


def _load_frames(frames_path):
    """load frame info"""
    pb_frames = loadSemFrame('{}/*.xml'.format(frames_path))
    return pb_frames


def _process_frames(frames):
    """extract only the frame name and sort"""
    result = [x[0] for x in frames]
    result.sort()
    return result


def _verify_name(names, pred_name):
    """verify the pred name is in the SORTED list of pred names"""
    idx = bisect_left(names, pred_name)
    return idx < len(names) and names[idx] == pred_name


def _filter_args_data(pb_names, args_data):
    """remove args data that are not in TreeBank"""
    pb_data = []
    for data in args_data:
        pred_name = data[1]
        if _verify_name(pb_names, pred_name):
            pb_data.append(data)

    return pb_data


def parse_dep_tree(frames_path, f):
    """
    main entry point
    read dependency tree file and construct a forest
    each tree represents a sentence
    trees appear in the forest in the order of the original sentences
    """
    sentences = read_sentences(f)
    pb_frames = _load_frames(frames_path)
    pb_names = _process_frames(pb_frames)

    forest = []
    for sentence in sentences:
        root = _parse_sentence(pb_names, sentence)
        forest.append(root)
    return forest


def read_back_sentence(sentence):
    nodes = []
    # construct a node for each word
    for word in sentence:
        node = TreeNode()
        node.value = word[2], word[1]
        nodes.append(node)

    # link the nodes into a tree
    root = None
    for i, word in enumerate(sentence):
        head_idx, rel = int(word[3]), word[4]
        if head_idx > 0:
            parent_idx = head_idx - 1
            if parent_idx > i:
                nodes[parent_idx].append_left_child(nodes[i], rel)
            else:
                nodes[parent_idx].append_right_child(nodes[i], rel)
        else:
            root = nodes[i]

    preds = []
    for i, word in enumerate(sentence):
        if word[5] != '_':
            pred_name = word[5]
            preds.append(nodes[i])
            nodes[i].frame = pred_name

    for n in preds:
        n.args = {}

    for i, word in enumerate(sentence):
        args = word[6:]
        for j, arg in enumerate(args):
            if arg != '_':
                preds[j].args[arg] = nodes[i]

    return root


def level_order_traversal(root):
    """
    :returns
    1st iteration: [[[root]]]
    following iterations:
    [[[left children], [right children]], [[], []], .. for each node from the
    previous level]
    """
    level = [[[root]]]
    while level:
        yield level
        cache = copy.copy(level)
        level = []
        for nodes in cache:
            for node in itertools.chain.from_iterable(nodes):
                x = node.flc
                lc = []  # left children
                while x is not None:
                    lc.append(x)
                    x = x.next_sib
                x = node.frc
                rc = []  # right children
                while x is not None:
                    rc.append(x)
                    x = x.next_sib
                node_children = [lc, rc]
                level.append(node_children)


def get_column_format(root):
    parent_id = 0
    par_column = []
    sib_column = []
    val_column = []
    has_left_child = []
    has_right_child = []
    has_sib = []
    for level in level_order_traversal(root):
        for branches in level:  # for each 2 branches from the previous node
            for branch in branches:
                for n in branch:
                    # parent id
                    par_column.append(parent_id)
                    # next sib exist?
                    if n.next_sib is not None:
                        sib_column.append(1)
                    else:
                        sib_column.append(0)
                    # value
                    val_column.append(n.info)
                    # has left child?
                    if n.flc is not None:
                        has_left_child.append(1)
                    else:
                        has_left_child.append(0)
                    # has right child?
                    if n.frc is not None:
                        has_right_child.append(1)
                    else:
                        has_right_child.append(0)
                    # has sib?
                    if len(branch) > 1:
                        has_sib.append(1)
                    else:
                        has_sib.append(0)
            parent_id += 1
    return (par_column, sib_column, val_column,
            has_left_child, has_right_child, has_sib)


if __name__ == '__main__':
    sentence = [[1, 'Ms.', 'NNP', 2, 'TITLE', '_', '_'],
                [2, 'Haag', 'NNP', 3, 'SBJ', '_', 'A0'],
                [3, 'plays', 'VBZ', 0, 'ROOT', 'play.02', '_'],
                [4, 'Elianti', 'NNP', 3, 'OBJ', '_', 'A1'],
                [5, '.', '.', 3, 'P', '_', '_']]
    root = read_back_sentence(sentence)
    x = get_column_format(root)
