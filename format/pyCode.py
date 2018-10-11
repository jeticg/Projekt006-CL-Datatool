import ast
from tree import Node


class _TmpNode:
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.children = []

    def __repr__(self):
        return 'TmpNode({}, {})'.format(self.tag, repr(self.value))


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
                else:
                    node.children.append(value)

        for i, child in enumerate(node.children):
            node.children[i] = _translate(child)

        return node


def _restructure_rec(node, orig_children):
    child_nodes = []
    for orig_child in orig_children:
        child_node = Node()
        child_node.value = (orig_child.tag, orig_child.value)
        child_nodes.append(child_node)
    for i, child_node in enumerate(child_nodes):
        child_node.parent = node
        if i == 0:
            node.child = child_node
        if i + 1 < len(child_nodes):
            # not last node
            child_node.sibling = child_nodes[i + 1]
    for child_node, orig_child in zip(child_nodes, orig_children):
        _restructure_rec(child_node, orig_child.children)


def _restructure(tmp_node):
    """transform the structure of TmpNode into Node"""
    node = Node()
    node.value = (tmp_node.tag, tmp_node.value)
    _restructure_rec(node, tmp_node.children)
    return node


def python_to_tree(code):
    py_ast = ast.parse(code)
    root = _translate(py_ast)
    res_root = _restructure(root)
    return res_root


if __name__ == '__main__':
    import sys

    if not bool(getattr(sys, 'ps1', sys.flags.interactive)):
        pass
    else:
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
            return 'Node({}, {})'.format(node.value[0], repr(node.value[1]))


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

        # draw_tmp_tree(root)
        # draw_res_tree(res_root)
