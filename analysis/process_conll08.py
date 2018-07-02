def read_sentences(file):
    lines = []
    for line in file:
        if line == '\n':
            yield lines
            lines.clear()
        else:
            lines.append(line.strip().split('\t'))


class TreeNode:
    def __init__(self, info, children=None):
        self.info = info
        if children is None:
            self.children = []
        else:
            self.children = children

    def __repr__(self):
        return f'TreeNode({self.info})'


FORM_OFFSET = 1
PPOS_OFFSET = 7
HEAD_OFFSET = 8
DEPREL_OFFSET = 9
PRED_OFFSET = 10
ARGS_OFFSET = 11


def is_pred(word):
    return word[PRED_OFFSET] != '_'


def parse_sentence(sentence):
    root = None
    nodes = []
    for word in sentence:
        nodes.append(TreeNode(word[FORM_OFFSET:PPOS_OFFSET + 1]))

    for i, word in enumerate(sentence):
        head_idx, rel = int(word[HEAD_OFFSET]), word[DEPREL_OFFSET]
        if head_idx > 0:
            nodes[head_idx - 1].children.append((nodes[i], rel))
        else:
            root = nodes[i]

    preds = []
    pred_names = []
    for i, word in enumerate(sentence):
        if is_pred(word):
            preds.append(nodes[i])
            pred_names.append(word[PRED_OFFSET])

    args_data = [(x, y, {}) for x, y in zip(preds, pred_names)]
    for i, word in enumerate(sentence):
        args = word[ARGS_OFFSET:]
        for j, arg in enumerate(args):
            if arg != '_':
                args_data[j][-1][arg] = nodes[i]

    return root, args_data


if __name__ == '__main__':
    with open('conll08st/data/train/train.closed') as file:
        sentences = read_sentences(file)
        sentence = next(sentences)
        root, args_data = parse_sentence(sentence)
