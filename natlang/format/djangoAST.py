from __future__ import print_function
import sys
import re
import astor
from natlang.format.pyCode import AstNode, python_to_tree, tree2ast
import tokenize
from io import StringIO
import os
import json
import copy
import keyword
import numbers

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


def de_canonicalize_code(code, ref_raw_code):
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


class DjangoAst(AstNode):
    def __init__(self):
        super(DjangoAst, self).__init__()
        self.raw_code = ''

    def export_for_eval(self):
        assert self.raw_code != ''
        py_ast = tree2ast(self)
        code = astor.to_source(py_ast).strip()
        decano_code = de_canonicalize_code(code, self.raw_code)
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


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]
    roots = []
    for line in content:
        entry = json.loads(line)
        raw_code = entry['raw_code']
        cano_code = entry['cano_code']
        root = python_to_tree(cano_code, DjangoAst)
        root.raw_code = raw_code
        roots.append(root)

    return roots


if __name__ == '__main__':
    loaded = load('/Users/ruoyi/Projects/PycharmProjects/data_fixer/' +
                  'django_exported/dev.jsonl')
