# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Django Dataset Code Loader class
# Simon Fraser University
# Ruoyi Wang
#
# For loading the code as a sequence of tokens
import tokenize as tk
import keyword
from io import StringIO
import os
import sys


def createSketch(tokens, sketchLabels, phGenerator):
    result = []
    for x in tokens:
        if x[0] == tk.NAME and not keyword.iskeyword(x[1]):
            x = 'NAME'
        elif x[0] == tk.STRING:
            x = 'STRING'
        elif x[0] == tk.NUMBER:
            x = 'NUMBER'
        else:
            x = x[1]
        result.append(x)
    return result


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        content = [line.strip() for line in f][:linesToLoad]

    ret = []
    for line in content:
        tokens = list(tk.generate_tokens(StringIO(line).readline))[:-1]
        ret.append(tokens)

    return ret


if __name__ == '__main__':
    loaded = load(
        '/Users/ruoyi/Projects/PycharmProjects/datatool/simple_code.txt')
    tokens = createSketch(loaded[0], None, None)
