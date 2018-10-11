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
