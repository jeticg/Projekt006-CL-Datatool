import re
import string
import json
from pprint import pprint

MARKER_NFA = re.compile(r'''<[A-Z_]+>''')


def split_tokens(line):
    line = line.strip()
    results = list(MARKER_NFA.finditer(line))

    indices = [0]
    for result in results:
        indices.extend(result.span())

    tokens = [line[i:j] for i, j in zip(indices, indices[1:] + [None])]
    return tokens


SBTK_START_MARKER = '__SP__ARG_START'
SBTK_END_MARKER = '__SP__ARG_END'
SEP_MARKER = '<TOKEN_SEPARATOR>'
FLAG_MARKER = '<FLAG_SUFFIX>'
STRANGE_MARKERS = ['UTILITY', 'Regex', 'Quantity']


def export_tokens(loaded_tokens):
    tokens = []
    types = []
    sbtk_on = False
    for tk in loaded_tokens:
        if tk == SEP_MARKER:
            pass
        elif tk == FLAG_MARKER:
            types[-1] = 'FLAG'
        elif tk == SBTK_START_MARKER:
            tokens.append('<SBTK_START>')
            types.append('SBTK_START')
            sbtk_on = True
        elif tk == SBTK_END_MARKER:
            tokens.append('<SBTK_END>')
            types.append('SBTK_END')
            sbtk_on = False
        elif tk in STRANGE_MARKERS:
            pass
        else:
            tokens.append(tk)
            if sbtk_on:
                types.append('SBTK')
            else:
                if tk in string.punctuation:
                    types.append('OP')
                elif tk.isnumeric():
                    types.append('NUM')
                else:
                    types.append('WORD')
    return tokens, types


def export(in_path, out_path):
    with open(in_path, 'r') as in_f, open(out_path, 'w') as out_f:
        for line in in_f:
            loaded_tokens = split_tokens(line)
            tokens, types = export_tokens(loaded_tokens)
            jsonl_entry = {'token': tokens, 'type': types}
            out_f.write(json.dumps(jsonl_entry))
            out_f.write('\n')


f = open('/Users/ruoyi/Projects/PycharmProjects/nl2bash/data/bash/dev.cm.partial.token')

IN_PATH = '/Users/ruoyi/Projects/PycharmProjects/nl2bash/data/bash'
OUT_PATH = '/Users/ruoyi/Projects/PycharmProjects/data_fixer/bash_exported'
IN_SUFFIX = '.cm.partial.token'
OUT_SUFFIX = '.jsonl'

for dataset in ['train', 'dev', 'test']:
    export('{}/{}{}'.format(IN_PATH, dataset, IN_SUFFIX),
           '{}/{}{}'.format(OUT_PATH, dataset, OUT_SUFFIX))

# lines = f.readlines()
# loaded_tokens = split_tokens(lines[0])
# tokens, types = export_tokens(loaded_tokens)
