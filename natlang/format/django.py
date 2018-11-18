from __future__ import print_function
import sys
import re
import os
from pyCode import python_to_tree


def line2code(l):
    p_elif = re.compile(r'^elif\s?')
    p_else = re.compile(r'^else\s?')
    p_try = re.compile(r'^try\s?')
    p_except = re.compile(r'^except\s?')
    p_finally = re.compile(r'^finally\s?')
    p_decorator = re.compile(r'^@.*')

    l = l.strip()
    if not l:
        return l

    if p_elif.match(l):
        l = 'if True: pass\n' + l
    if p_else.match(l):
        l = 'if True: pass\n' + l

    if p_try.match(l):
        l = l + 'pass\nexcept: pass'
    elif p_except.match(l):
        l = 'try: pass\n' + l
    elif p_finally.match(l):
        l = 'try: pass\n' + l

    if p_decorator.match(l):
        l = l + '\ndef dummy(): pass'
    if l[-1] == ':':
        l = l + 'pass'

    # parse = ast.parse(l)
    return l


def load(fileName, linesToLoad=sys.maxsize, verbose=True, option=None):
    """
    WARNING: this function assumes `[PREFIX].token_maps.pkl` is in the same
    directory as the code file `token_maps.pkl` should be a {int->[str]}
    mapping of copied words
    """
    import progressbar
    fileName = os.path.expanduser(fileName)

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
        if not line:
            print('line {} is empty'.format(i))
        code = line2code(line)
        roots.append(python_to_tree(code))
        if i == linesToLoad:
            break

    if verbose is True:
        loadProgressBar.finish()

    return roots


if __name__ == '__main__':
    from graphviz import Graph
    import os
    import errno


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


    roots = load('/Users/ruoyi/Projects/PycharmProjects/NMT-Experiments/data/django/test.code')
