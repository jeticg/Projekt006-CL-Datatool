# -*- coding: utf-8 -*-
# Python version: 3.6
# clevr loader

from __future__ import absolute_import
import io
import os
import sys
import natlang as nl


        #(', 'Root', '(', 'count', '(', 'same_shape', 
        # '(', 'unique', '(', 'filter_material_rubber', 
        # '(', 'filter_color_cyan', 
        # '(', 'filter_size_small', ...]
    
def constructTree(elements, rootLabel="ROOT"):
    '''
    This method constructs a tree from a list of elements. Each bracket is
    considered an independent element.
    @param elements: list of str, in Penn Treebank format
    @return root: AstNode, the root node.
    '''
    root = None
    currentParent = None
    current = None
    for element in elements:
        if element == "(":
            currentParent = current
            current = nl.format.astTree.AstNode(parent=currentParent)
            if currentParent is not None:
                if currentParent.child is not None:
                    tmp = currentParent.child
                    while tmp.sibling is not None:
                        tmp = tmp.sibling
                    tmp.sibling = current
                else:
                    currentParent.child = current
            else:
                root = current

        elif element == ")":
            current = current.parent
            if current is not None:
                currentParent = current.parent
        else:
            current.value += (element,) # back to branch node, add ')'?
            if element == 'scene':
                current.value += ("",)
    if root is not None:
        if root.value == ():
            root.value = (rootLabel,)
        # try:
        #     root.refresh()
        # except RuntimeError:
        #     return None
    return root


class Code:
    """
    __init__(self, tokens)
    """
    placeHolders = ['NAME', 'STRING', 'NUMBER']

    def __init__(self, tokens):
        self.value = tokens
        self.astTree = None

        root = constructTree(tokens)
        #self.bfs(root, 1)
        self.astTree=root

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __repr__(self):
        return "<ClevrCode: " + str(self.value) + ">"

    def __getitem__(self, key):
        return self.value[key]

    def export(self):
        return " ".join(self.value)

    def bfs(root, id=1):
        nodes=[]
        stack = [root]

        while stack:
            cur_node = stack[0]
            stack = stack[1:]
            nodes.append(cur_node)
            cur_node.id = id
            id = id+1
            if cur_node.sibling is not None:
                stack.append(cur_node.sibling)
                #cur_node = cur_node.sibling
            if cur_node.child is not None:
                stack.append(cur_node.child)
        return

def load(file, linesToLoad=sys.maxsize, verbose=True):
    import progressbar
    widgets = [progressbar.Bar('>'), ' ', progressbar.ETA(),
               progressbar.FormatLabel(
               '; Total: %(value)d sents (in: %(elapsed)s)')]

    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]
    result = []
    if verbose is True:
        loadProgressBar =\
            progressbar.ProgressBar(widgets=widgets,
                                    maxval=len(content)).start()

    for i, line in enumerate(content):
        entry = line.split()
        try:
            result.append(Code(entry))
        except SyntaxError:
            result.append(None)
        if verbose is True:
            loadProgressBar.update(i)

    if verbose is True:
        loadProgressBar.finish()
    return result

if __name__ == '__main__':
    loaded = load('/local-scratch/yuer/ProjectMay/Projekt005-CL-CodeGen/'
                    +'clevr/train.nodes1000')