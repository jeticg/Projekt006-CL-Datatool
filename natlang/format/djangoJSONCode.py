# -*- coding: utf-8 -*-
# Python version: 3
#
# Django Dataset Code Loader class
# For django code stored in JSON format as provided by Yin et Neubig, 2017
# Simon Fraser University
# Ruoyi Wang, Jetic Gū
#
# For loading the code as a sequence of tokens
import json
import re
import os
import sys
import copy
import keyword
import numbers
import tokenize
import astor
from io import StringIO

from natlang.format.pyCode import AstNode, python2astTree, tree2ast

builtin_fns = (
    'abs', 'delattr', 'hash', 'memoryview', 'set', 'all', 'dict', 'help',
    'min', 'setattr', 'any', 'dir', 'hex', 'next', 'slice', 'ascii', 'divmod',
    'id', 'object', 'sorted', 'bin', 'enumerate', 'input', 'oct',
    'staticmethod', 'bool', 'eval', 'int', 'open', 'str', 'breakpoint', 'exec',
    'isinstance', 'ord', 'sum', 'bytearray', 'filter', 'issubclass', 'pow',
    'super', 'bytes', 'float', 'iter', 'print', 'tuple', 'callable', 'format',
    'len', 'property', 'type', 'chr', 'frozenset', 'list', 'range', 'vars',
    'classmethod', 'getattr', 'locals', 'repr', 'zip', 'compile', 'globals',
    'map', 'reversed', '__import__', 'complex', 'hasattr', 'max', 'round')

p_elif = re.compile(r'^elif\s?')
p_else = re.compile(r'^else\s?')
p_try = re.compile(r'^try\s?')
p_except = re.compile(r'^except\s?')
p_finally = re.compile(r'^finally\s?')
p_decorator = re.compile(r'^@.*')
masked_str = re.compile(r'''^_STR:\d+_$''')


class Code:
    def __init__(self, tokens, valueTypes, canoCode=None):
        self.value = tokens
        self.valueTypes = valueTypes
        assert len(self.value) == len(self.valueTypes)
        self.sketch = []
        self.createSketch()  # writes to self.sketch
        if canoCode is None:
            self.astTree = None
            self.canoCode = None
        else:
            self.canoCode = canoCode
            self.astTree = python2astTree(canoCode, DjangoAst)
        return

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __repr__(self):
        return "<DjangoCode: " + str(self.value) + ">"

    def __getitem__(self, key):
        return self.value[key]

    def createSketch(self):
        self.sketch = []
        for tk, ty in zip(self.value, self.valueTypes):
            if ty in ('NAME', 'STRING', 'NUMBER'):
                self.sketch.append(ty)
            else:
                self.sketch.append(tk)

    def export(self):
        return " ".join(self.value)


class DjangoAst(AstNode):
    def __init__(self):
        super(DjangoAst, self).__init__()
        self.raw_code = ''

    def export_for_eval(self):
        assert self.raw_code != ''
        py_ast = tree2ast(self)
        code = astor.to_source(py_ast).strip()
        decano_code = decanonicaliseCode(code, self.raw_code)
        tokens = tokenize.generate_tokens(StringIO(decano_code).readline)
        tokens = [x[1] for x in tokens]
        # todo: replace special tokens?
        return tokens[:-1]

    def createSketch(self):
        """
        return the root of a new tree with sketches the sketch tree cannot be
        converted back to python unless all sketch holes are filled
        """
        assert self.raw_code != ''
        root = copy.deepcopy(self)
        leaves = root.find_literal_nodes()
        for leaf in leaves:
            if isinstance(leaf.value[1], numbers.Number):
                leaf.value = leaf.value[0], 'NUMBER'
            else:
                if masked_str.match(leaf.value[1]):
                    leaf.value = leaf.value[0], 'STRING'
                elif keyword.iskeyword(leaf.value[1]) or\
                        leaf.value[1] in builtin_fns:
                    continue
                else:
                    leaf.value = leaf.value[0], 'NAME'
        return root

    def visualize(self, name='res'):
        from graphviz import Graph
        import os
        import errno

        def repr_n(node):
            return 'Node{}'.format(repr(node.value))

        try:
            os.makedirs('figures')
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

        fname = 'figures/{}'.format(name + '.gv')
        g = Graph(format='png', filename=fname)
        g.attr(rankdir='BT')

        fringe = [self]
        while fringe:
            node = fringe.pop()
            g.node(str(id(node)), repr_n(node))
            if node.child is not None:
                child = node.child
                fringe.append(child)
                g.node(str(id(child)), repr_n(node))

            if node.sibling is not None:
                sibling = node.sibling
                fringe.append(sibling)
                g.node(str(id(sibling)), repr_n(node))

            if node.parent is not None:
                g.edge(str(id(node)), str(id(node.parent)))

        return g.render()


def decanonicaliseCode(code, ref_raw_code):
    if code.endswith('def dummy():\n    pass'):
        code = code.replace('def dummy():\n    pass', '').strip()

    if p_elif.match(ref_raw_code):
        # remove leading if true
        code = code.replace('if True:\n    pass', '').strip()
    elif p_else.match(ref_raw_code):
        # remove leading if true
        code = code.replace('if True:\n    pass', '').strip()

    # try/catch/except stuff
    if p_try.match(ref_raw_code):
        code = code.replace('except:\n    pass', '').strip()
    elif p_except.match(ref_raw_code):
        code = code.replace('try:\n    pass', '').strip()
    elif p_finally.match(ref_raw_code):
        code = code.replace('try:\n    pass', '').strip()

    # remove ending pass
    if code.endswith(':\n    pass'):
        code = code[:-len('\n    pass')]

    return code


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]
    result = []
    for line in content:
        entry = json.loads(line)
        result.append(
            Code(entry['token'], entry['type'], canoCode=entry["cano_code"]))
    return result


if __name__ == '__main__':
    loaded = load('/Users/ruoyi/Projects/PycharmProjects/data_fixer/' +
                  'django_exported/dev.jsonl')
