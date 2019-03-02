import json
import os
import sys
# import bashlex
from natlang.format.astTree import AstNode as BaseNode


class Code:
    def __init__(self, tokens, valueTypes, canoCode=None):
        self.value = tokens
        self.valueTypes = valueTypes
        assert len(self.value) == len(self.valueTypes)
        self.sketch = []
        self.createSketch()  # writes to self.sketch

    def __iter__(self):
        return iter(self.value)

    def __len__(self):
        return len(self.value)

    def __repr__(self):
        return "<BashCode: " + str(self.value) + ">"

    def __getitem__(self, key):
        return self.value[key]

    def createSketch(self):
        self.sketch = []
        for tk, ty in zip(self.value, self.valueTypes):
            if ty in ('WORD', 'FLAG', 'NUM', 'SBTK'):
                self.sketch.append(ty)
            else:
                self.sketch.append(tk)

    def export(self):
        return " ".join(self.value)


class AstNode(BaseNode):
    # FIXME: WIP
    def find_literal_nodes(self):
        if self.value[0] == 'LITERAL':
            return [self]
        else:
            nodes = []
            node = self.child
            while node is not None:
                nodes.extend(node.find_literal_nodes())
                node = node.sibling
            return nodes

    def export(self):
        pass


class _TmpNode:
    # FIXME: WIP
    def __init__(self, tag, value):
        self.tag = tag
        self.value = value
        self.children = []

    def __repr__(self):
        return 'TmpNode({}, {})'.format(repr(self.tag), repr(self.value))


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]
    result = []
    for line in content:
        entry = json.loads(line)
        result.append(
            Code(entry['token'], entry['type']))
    return result


if __name__ == '__main__':
    loaded = load('/Users/ruoyi/Projects/PycharmProjects/data_fixer/' +
                  'bash_exported/dev.jsonl')
