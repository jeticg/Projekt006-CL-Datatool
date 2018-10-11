from __future__ import unicode_literals
from io import open

fpath =\
    '/Users/ruoyi/Projects/PycharmProjects/NMT-Experiments/data/ASPEC/' +\
    'ASPEC-JE/train/train-1.txt'

with open(fpath, 'r', encoding='utf8') as infile, \
        open('jpn.txt', 'w', encoding='utf8') as jpn_file, \
        open('train.tree.en', 'w', encoding='utf8') as eng_file:
    for line in infile:
        vec = line.split('|||')
        jpn = vec[3].strip()
        eng = vec[-1].strip()
        jpn_file.write(jpn)
        jpn_file.write('\n')
        eng_file.write(eng)
        eng_file.write('\n')
