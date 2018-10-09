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
        g.node(str(id(node)), repr(node))
        if node.first_child is not None:
            child = node.first_child
            fringe.append(child)
            g.node(str(id(child)), repr(node))
            g.edge(str(id(node)), str(id(child)), color='red')

        if node.next_sibling is not None:
            sibling = node.next_sibling
            fringe.append(sibling)
            g.node(str(id(sibling)), repr(node))
            g.edge(str(id(node)), str(id(sibling)), color='blue')

        if node.parent is not None:
            g.edge(str(id(node)), str(id(node.parent)), color='green')

    return g.render()
