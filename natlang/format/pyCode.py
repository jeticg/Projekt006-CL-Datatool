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
    code = r"os.path.abspath('mydir/myfile.txt')"
    py_ast = ast.parse(code)
    root = _translate(py_ast)
    res_root = _restructure(root)
    from test import tree_viz

    tree_viz.draw_tmp_tree(root)
    tree_viz.draw_res_tree(res_root)
