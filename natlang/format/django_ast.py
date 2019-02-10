from __future__ import print_function
import sys
import re
import astor
from natlang.format.pyCode import AstNode, python_to_tree, tree2ast
import tokenize
from io import StringIO
import os, json

p_elif = re.compile(r'^elif\s?')
p_else = re.compile(r'^else\s?')
p_try = re.compile(r'^try\s?')
p_except = re.compile(r'^except\s?')
p_finally = re.compile(r'^finally\s?')
p_decorator = re.compile(r'^@.*')


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
        tokens = [x[1] for x in tokenize.generate_tokens(StringIO(decano_code).readline)]
        # todo: replace special tokens?
        return tokens[:-1]

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
    loaded = load(
        '/Users/ruoyi/Projects/PycharmProjects/data_fixer/django_exported/dev.jsonl')
