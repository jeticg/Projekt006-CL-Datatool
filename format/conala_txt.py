from __future__ import print_function

import re
import sys
import os


def load(file, linesToLoad=sys.maxsize):
    nfa = re.compile(r'`[^`]+`|[^\s]+')

    data = []
    copied_tokens = []
    with open(os.path.expanduser(file)) as f:
        for i, line in enumerate(f):
            words = []
            tokens = []
            for word in nfa.findall(line):
                if word.startswith('`') and word.endswith('`'):
                    # annotated content
                    word = word.strip('`')

                    if (word.startswith('"') and word.endswith('"')) \
                            or (word.startswith("'") and word.endswith("'")):
                        # string literal
                        tokens.append(word)
                        word = '<STR_LITERAL>'
                    else:
                        # variable name / other literal
                        tokens.append(word)
                        word = '<VAR>'
                else:
                    word = word.lower()
                words.append(word)

            data.append(words)
            copied_tokens.append(tokens)
            if i >= linesToLoad:
                break
    return data, copied_tokens


if __name__ == '__main__':
    data, copied_tokens = load('/Users/ruoyi/Projects/PycharmProjects/datatool/test/sampleConalaTxt.txt')
    print(data)
    print(copied_tokens)
