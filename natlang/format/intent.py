# -*- coding: utf-8 -*-
# Python version: 2/3
#
# Django Dataset Intention Loader class
# Simon Fraser University
# Ruoyi Wang
#
# For loading the intentions as a sequence of natural language tokens
import re
import sys
import os

tokenize_nfa = re.compile(r'''
((?<=\W)"(?:\\"|[^"])*"(?=\W)|(?<=\W)'(?:\\'|[^'])*'(?=\W))|    # str
`([^`]+)`|    # annotated
([^\s]+)    # other stuff
''', re.VERBOSE)

str_checker = re.compile(r'''("(\\"|[^"])*")|('(\\'|[^'])*')''')
word_checker = re.compile(r'''^[a-zA-Z][a-z]*$''')


class Intent:
    def __init__(self, line):
        self.orig_line = line
        self.value = []
        self.orig_tokens = {}
        self.parse()

    def parse(self):
        matches = tokenize_nfa.finditer(' ' + self.orig_line)  # add a safe blank to the front
        for m in matches:
            groups = [(category, lexeme) for category, lexeme in enumerate(m.groups()) if lexeme is not None]
            if len(groups) > 1:
                raise RuntimeError("Multiple match in groups {}".format(groups))
            else:
                category, lexeme = groups[0]

            if category == 0:
                # str literal
                self.value.append('<STR_LITERAL>')
                self.orig_tokens[len(self.value) - 1] = eval(lexeme)
            elif category == 1:
                # annotated content
                if str_checker.match(lexeme):
                    self.value.append('<STR_LITERAL>')
                    self.orig_tokens[len(self.value) - 1] = eval(lexeme)
                elif lexeme.isnumeric():
                    self.value.append('<NUM>')
                    self.orig_tokens[len(self.value) - 1] = lexeme
                else:
                    self.add_var(lexeme)
            else:
                punc = None
                if not lexeme[-1].isalpha():
                    # punctuations
                    punc = lexeme[-1]
                    if lexeme[:-1]:
                        lexeme = lexeme[:-1]
                    else:
                        # pure punctuation
                        self.value.append(punc)
                        continue

                if not word_checker.match(lexeme):
                    # best-effort var detection
                    self.add_var(lexeme)
                else:
                    if lexeme.endswith("\'s"):
                        # 's
                        if lexeme[:-2]:
                            self.value.append(lexeme[:-2].lower())
                        self.value.append("'s")
                    else:
                        # normal word
                        self.value.append(lexeme.lower())

                if punc is not None:
                    self.value.append(punc)

    def add_var(self, lexeme):
        """split dots in variable names"""
        tokens = lexeme.split('.')
        for i, token in enumerate(tokens):
            self.value.append('<VAR>')
            self.orig_tokens[len(self.value) - 1] = token
            if i != len(tokens) - 1:
                # not last tokens
                self.value.append('.')

    def __iter__(self):
        return iter([t for t in self.value])

    def __len__(self):
        return len(self.value)

    def __getitem__(self, item):
        return self.value[item]

    def __repr__(self):
        return "<Intent: " + str([t for t in self.value]) + ">"

    def export(self):
        return " ".join([t for t in self.value])


def load(file, linesToLoad=sys.maxsize):
    with open(os.path.expanduser(file)) as f:
        lines = [line for line in f][:linesToLoad]

    return [Intent(line) for line in lines]


if __name__ == '__main__':
    results = load('/Users/ruoyi/Projects/PycharmProjects/datatool/natlang/test/sampleDjangoAnno.txt')
    f = open('/Users/ruoyi/Projects/PycharmProjects/datatool/natlang/test/sampleDjangoAnno.txt')
    lines = list(f)

    line = lines[0]
    matches = tokenize_nfa.finditer(line)
    matches = list(matches)
    from pprint import pprint

    matches[-7].groups()
