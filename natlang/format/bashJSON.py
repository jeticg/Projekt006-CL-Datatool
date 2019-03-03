import json
import os
import sys
import bashlex
import itertools
import re
from operator import itemgetter
from natlang.format.astTree import AstNode as BaseNode


class Code:
    def __init__(self, tokens, valueTypes, canoCode=None):
        self.value = tokens
        self.valueTypes = valueTypes
        assert len(self.value) == len(self.valueTypes)
        self.sketch = []
        self.createSketch()  # writes to self.sketch

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __repr__(self):
        return "<BashCode: " + str(self.value) + ">"

    def __getitem__(self, key):
        return self.value[key]

    def createSketch(self):
        self.sketch = []
        for tk, ty in zip(self.value, self.valueTypes):
            if ty in ('WORD', 'FLAG', 'NUM', 'SBTK'):
                self.sketch.append(ty)
            else:
                self.sketch.append(tk)

    def export(self):
        return " ".join(self.value)


def proc_line(line):
    parts = bashlex.parse(line)
    assert len(parts) == 1
    ast = parts[0]
    return ast


def determine_pst_type(pst_str):
    if pst_str.startswith('<(') and pst_str.endswith(')'):
        pst_type = 'PST_left'
    elif pst_str.startswith('>(') and pst_str.endswith(')'):
        pst_type = 'PST_right'
    else:
        pst_type = 'unknown'
    return pst_type


def remap_pos(node, cst_node, line):
    """remap the pos of a command substitution node `cst_node` to its parent node `node`"""
    cst_str = line[slice(*cst_node.pos)]
    remapped_start = node.word.find(cst_str)
    remapped_end = remapped_start + len(cst_str)
    return remapped_start, remapped_end


def split_segments(node, pos_list):
    """
    :param node: Node of type word
    :param pos_list: [((start:int, end:int), type_name:str, node)] pos of special parts
    :return: [(type_name: str, {text_segment: str | node})]
    """
    pos_list.sort(key=itemgetter(0))
    segments = []
    last_end = 0
    for t in pos_list:
        pos, type_name, part = t
        text_segment = node.word[last_end:pos[0]]
        last_end = pos[1]
        if text_segment:
            segments.append(('text', text_segment))
        # node_text = node.word[slice(*pos)]
        segments.append((type_name, part))
    text_segment = node.word[last_end:]
    if text_segment:
        segments.append(('text', text_segment))
    return segments


sbtk_engine = re.compile(r'''
[a-zA-Z]+ | # words
[0-9]+ |    # numbers
.   # everything else
''', re.VERBOSE)


def split_subtoken(text):
    """
    :param text: str
    :return: [str]
    """
    return sbtk_engine.findall(text)


CST_KIND = 'commandsubstitution'
PST_KIND = 'processsubstitution'


def process_node(node, line):
    if node.kind == 'word':
        pos_list = []
        for part in node.parts:
            if part.kind in ('parameter', 'tilde'):
                pass
            else:
                remapped_pos = remap_pos(node, part, line)
                if part.kind == CST_KIND:
                    # cst_type = determine_cst_type(part_str)
                    type_name = 'CST'
                elif part.kind == PST_KIND:
                    part_str = node.word[slice(*remapped_pos)]
                    pst_type = determine_pst_type(part_str)
                    type_name = pst_type
                else:
                    raise RuntimeError('unknown kind {}'.format(part.kinds))
                assert type_name != 'unknown'
                pos_list.append((remapped_pos, type_name, part))
        segments = split_segments(node, pos_list)

        children = []
        for segment in segments:
            ty, data = segment
            if ty == 'text':
                subtokens = split_subtoken(data)  # todo: wrap each subtoken in a node
                children.append(subtokens)
            else:
                children.append(data)  # todo: transform data recursively
        return children


class AstNode(BaseNode):
    # FIXME: WIP
    def find_literal_nodes(self):
        if self.value[0] == 'LITERAL':
            return [self]
        else:
            nodes = []
            node = self.child
            while node is not None:
                nodes.extend(node.find_literal_nodes())
                node = node.sibling
            return nodes

    def export(self):
        pass


class _TmpNode:
    # FIXME: WIP
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.children = []

    def __repr__(self):
        return 'TmpNode({}, {})'.format(repr(self.tag), repr(self.value))


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]
    result = []
    for line in content:
        entry = json.loads(line)
        result.append(
            Code(entry['token'], entry['type']))
    return result


if __name__ == '__main__':
    loaded = load('/Users/ruoyi/Projects/PycharmProjects/data_fixer/' +
                  'bash_exported/dev.jsonl')
