# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Python format Code (CoNaLa) loader
# Simon Fraser University
# Ruoyi Wang
#
#
from __future__ import absolute_import, print_function
import ast
import sys
import os

try:
    from tree import Node as TreeNode
except ImportError:
    from natlang.format.tree import Node as TreeNode


def export_tokens(node):
    if node is None:
        # guard against incomplete tree
        return []
    elif node.value[0] == 'LITERAL':
        return [node.value[1]]
    elif node.value[0] == 'DUMMY':
        return []
    elif node.value[0] == 'Attribute':
        vec = []
        vec.extend(export_tokens(node.child))
        vec.append('.')
        if node.child is not None:
            vec.extend(export_tokens(node.child.sibling))
        return vec
    elif node.value[0] == 'Call':
        vec = []
        vec.extend(export_tokens(node.child))
        vec.append('(')
        if node.child is not None:
            n = node.child.sibling
            while n is not None:
                vec.extend(export_tokens(n))
                n = n.sibling
        vec.append(')')
        return vec
    else:
        vec = []
        n = node.child
        while n is not None:
            vec.extend(export_tokens(n))
            n = n.sibling
        return vec


class AstNode(TreeNode):
    def __repr__(self):
        return 'AstNode({})'.format(repr(self.value))


class _TmpNode:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.children = []

    def __repr__(self):
        return 'TmpNode({}, {})'.format(repr(self.tag), repr(self.value))


def _translate(py_ast):
    """translate python ast into custom class TmpNode"""
    ignore_list = ('lineno', 'col_offset', 'ctx')

    if isinstance(py_ast, _TmpNode):
        for i, child in enumerate(py_ast.children):
            py_ast.children[i] = _translate(child)
        return py_ast
    elif not isinstance(py_ast, ast.AST):
        # literal
        return _TmpNode('LITERAL', py_ast)
    else:
        node = _TmpNode(py_ast.__class__.__name__, None)
        for field, value in ast.iter_fields(py_ast):
            if field not in ignore_list:
                if isinstance(value, list):
                    # star-production
                    # this child is a list
                    # transform into a standalone node
                    vec_child = _TmpNode(field + '_vec', None)
                    vec_child.children = list(value)
                    node.children.append(vec_child)
                elif value is None:
                    # optional-production
                    vec_child = _TmpNode(field + '_optional', None)
                    node.children.append(vec_child)
                else:
                    node.children.append(value)

        for i, child in enumerate(node.children):
            node.children[i] = _translate(child)

        return node


def _restructure_rec(node, orig_children):
    """
    `node` is the already transformed node (type=tree.Node)
    `orig_children` is a list of the children corresponds to `node`
        (type=[TmpNode])
    """
    # edge case
    tag = node.value[0]
    if (tag.endswith('_vec') or tag.endswith('_optional')) and \
            not orig_children:
        # transformed grammar with no children
        dummy = AstNode()
        dummy.value = ('DUMMY', None)
        node.child = dummy
        dummy.parent = node

    # transform each child node
    child_nodes = []
    for orig_child in orig_children:
        child_node = AstNode()
        if orig_child.value is None:
            # internal node
            child_node.value = (orig_child.tag,)
        else:
            # leaf node
            child_node.value = (orig_child.tag, orig_child.value)
        child_nodes.append(child_node)

    # link child nodes
    for i, child_node in enumerate(child_nodes):
        child_node.parent = node
        if i == 0:
            node.child = child_node
        if i + 1 < len(child_nodes):
            # not last node
            child_node.sibling = child_nodes[i + 1]

    # recurse
    for child_node, orig_child in zip(child_nodes, orig_children):
        _restructure_rec(child_node, orig_child.children)


def _restructure(tmp_node):
    """transform the structure of TmpNode into Node"""
    node = AstNode()
    if tmp_node.value is None:
        node.value = (tmp_node.tag,)
    else:
        node.value = (tmp_node.tag, tmp_node.value)

    _restructure_rec(node, tmp_node.children)

    # append topmost root node
    root = AstNode()
    root.value = ('ROOT',)
    root.child = node
    node.parent = root
    return root


def python_to_tree(code):
    py_ast = ast.parse(code)
    root = _translate(py_ast)
    res_root = _restructure(root)
    res_root.calcId(1)
    res_root.calcPhrase(force=True)
    return res_root


def _find_literal_nodes(ast_tree):
    if ast_tree.value[0] == 'LITERAL':
        return [ast_tree]
    else:
        nodes = []
        node = ast_tree.child
        while node is not None:
            nodes.extend(_find_literal_nodes(node))
            node = node.sibling
        return nodes


def load(fileName, linesToLoad=sys.maxsize, verbose=True, option=None):
    """WARNING: this function assumes `[PREFIX].token_maps.pkl` is in the same directory as the code file
    `token_maps.pkl` should be a {int->[str]} mapping of copied words"""
    import progressbar
    import cPickle as pickle
    import itertools
    orig_name = os.path.basename(fileName)
    fileName = os.path.expanduser(fileName)

    if option is None:
        option = {}
        option['mapping_path'] = os.path.dirname(os.path.abspath(fileName)) + '/{}.token_maps.pkl'.format(
            orig_name.rstrip('.snippets.txt'))
    print(option['mapping_path'])

    with open(option['mapping_path']) as mapping_f:
        token_maps = pickle.load(mapping_f)

    roots = []
    i = 0
    widgets = [progressbar.Bar('>'), ' ', progressbar.ETA(),
               progressbar.FormatLabel(
                   '; Total: %(value)d sents (in: %(elapsed)s)')]
    if verbose is True:
        loadProgressBar = \
            progressbar.ProgressBar(widgets=widgets,
                                    maxval=min(
                                        sum(1 for line in open(fileName)),
                                        linesToLoad)).start()
    for line in open(fileName):
        i += 1
        if verbose is True:
            loadProgressBar.update(i)
        code = eval(line)
        roots.append(python_to_tree(code))
        if i == linesToLoad:
            break

    for root, tokens_map in itertools.izip_longest(roots, token_maps, fillvalue=[]):
        literal_nodes = _find_literal_nodes(root)
        for node in literal_nodes:
            if node.value[1] in tokens_map.values():
                node.value = node.value[0], '<COPIED>'

    if verbose is True:
        loadProgressBar.finish()

    return roots


if __name__ == '__main__':
    # if not bool(getattr(sys, 'ps1', sys.flags.interactive)):
    #     pass
    # else:
    # viz tools
    from graphviz import Graph
    import os
    import errno


    def draw_tmp_tree(root, name='tmp'):
        try:
            os.makedirs('figures')
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

        fname = 'figures/{}'.format(name + '.gv')
        g = Graph(format='png', filename=fname)

        fringe = [root]
        while fringe:
            node = fringe.pop()
            g.node(str(id(node)), repr(node))
            for child in node.children:
                fringe.append(child)
                g.node(str(id(child)), repr(node))
                g.edge(str(id(node)), str(id(child)))

        return g.render()


    def repr_n(node):
        return 'Node{}'.format(repr(node.value))


    def draw_res_tree(root, name='res'):
        try:
            os.makedirs('figures')
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise

        fname = 'figures/{}'.format(name + '.gv')
        g = Graph(format='png', filename=fname)

        fringe = [root]
        while fringe:
            node = fringe.pop()
            g.node(str(id(node)), repr_n(node))
            if node.child is not None:
                child = node.child
                fringe.append(child)
                g.node(str(id(child)), repr_n(node))
                g.edge(str(id(node)), str(id(child)), color='red')

            if node.sibling is not None:
                sibling = node.sibling
                fringe.append(sibling)
                g.node(str(id(sibling)), repr_n(node))
                g.edge(str(id(node)), str(id(sibling)), color='blue')

            if node.parent is not None:
                g.edge(str(id(node)), str(id(node.parent)), color='green')

        return g.render()


    # example data structures
    code = r"os.path.abspath('mydir/myfile.txt')"
    py_ast = ast.parse(code)
    root = _translate(py_ast)
    res_root = _restructure(root)
    print(export_tokens(res_root))

    # draw_tmp_tree(root)
    # draw_res_tree(res_root)
