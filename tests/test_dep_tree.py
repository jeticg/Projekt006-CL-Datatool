import os
import sys
import inspect
import unittest
currentdir =\
    os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir)
from dep_tree import parse_dep_tree, export_to_table,\
    read_back_sentence, level_order_traversal, get_column_format


class TestParse(unittest.TestCase):
    def setUp(self):
        with open('../support/sampleDepTree.txt') as file:
            self.forest = parse_dep_tree('../data/pb_frames', file)

    def test_parse(self):
        correct_0 = [[1, 'Ms.', 'NNP', 2, 'TITLE', '_', '_'],
                     [2, 'Haag', 'NNP', 3, 'SBJ', '_', 'A0'],
                     [3, 'plays', 'VBZ', 0, 'ROOT', 'play.02', '_'],
                     [4, 'Elianti', 'NNP', 3, 'OBJ', '_', 'A1'],
                     [5, '.', '.', 3, 'P', '_', '_']]

        correct_1 = [[1, 'Bell', 'NNP', 8, 'SBJ', '_', 'A1', 'A0', 'A0'],
                     [2, ',', ',', 1, 'P', '_', '_', '_', '_'],
                     [3, 'based', 'VBN', 1, 'APPO', 'base.01', '_', '_', '_'],
                     [4, 'in', 'IN', 3, 'LOC', '_', 'AM-LOC', '_', '_'],
                     [5, 'Los', 'NNP', 6, 'NAME', '_', '_', '_', '_'],
                     [6, 'Angeles', 'NNP', 4, 'PMOD', '_', '_', '_', '_'],
                     [7, ',', ',', 1, 'P', '_', '_', '_', '_'],
                     [8, 'makes', 'VBZ', 0, 'ROOT', 'make.01', '_', '_', '_'],
                     [9, 'and', 'CC', 8, 'COORD', '_', '_', '_', '_'],
                     [10, 'distributes', 'VBZ', 9, 'CONJ', 'distribute.01', '_', '_', '_'],
                     [11, 'electronic', 'JJ', 16, 'NMOD', '_', '_', '_', '_'],
                     [12, ',', ',', 11, 'P', '_', '_', '_', '_'],
                     [13, 'computer', 'NN', 11, 'COORD', '_', '_', '_', '_'],
                     [14, 'and', 'CC', 13, 'COORD', '_', '_', '_', '_'],
                     [15, 'building', 'NN', 14, 'CONJ', '_', '_', '_', '_'],
                     [16, 'products', 'NNS', 8, 'OBJ', '_', '_', 'A1', 'A1'],
                     [17, '.', '.', 8, 'P', '_', '_', '_', '_']]
        self.assertEqual(export_to_table(self.forest[0]), correct_0)
        self.assertEqual(export_to_table(self.forest[1]), correct_1)

    def test_read_back(self):
        tree = self.forest[1]
        original_dump = export_to_table(tree)
        new_tree = read_back_sentence(original_dump)
        new_dump = export_to_table(new_tree)
        self.assertEqual(original_dump, new_dump)


class TestColumnFormat(unittest.TestCase):
    def test_level_order_traversal(self):
        sentence = [[1, 'Ms.', 'NNP', 2, 'TITLE', '_', '_'],
                    [2, 'Haag', 'NNP', 3, 'SBJ', '_', 'A0'],
                    [3, 'plays', 'VBZ', 0, 'ROOT', 'play.02', '_'],
                    [4, 'Elianti', 'NNP', 3, 'OBJ', '_', 'A1'],
                    [5, '.', '.', 3, 'P', '_', '_']]
        root = read_back_sentence(sentence)
        self.assertEqual([
            [[[root]]],
            [[[root.flc], [root.frc, root.frc.next_sib]]],
            [[[root.flc.flc], []], [[], []], [[], []]],
            [[[], []]]
        ],
            list(level_order_traversal(root)))

    def test_column_format(self):
        sentence = [[1, 'Ms.', 'NNP', 2, 'TITLE', '_', '_'],
                    [2, 'Haag', 'NNP', 3, 'SBJ', '_', 'A0'],
                    [3, 'plays', 'VBZ', 0, 'ROOT', 'play.02', '_'],
                    [4, 'Elianti', 'NNP', 3, 'OBJ', '_', 'A1'],
                    [5, '.', '.', 3, 'P', '_', '_']]
        root = read_back_sentence(sentence)
        self.assertEqual(([0, 1, 1, 1, 2],
                          [0, 0, 1, 0, 0],
                          [('VBZ', 'plays'), ('NNP', 'Haag'), ('NNP', 'Elianti'), ('.', '.'), ('NNP', 'Ms.')],
                          [1, 1, 0, 0, 0],
                          [1, 0, 0, 0, 0],
                          [0, 0, 1, 1, 0]),
                         get_column_format(root))

    def test_column_format_complex(self):
        sentence = [[1, 'Bell', 'NNP', 8, 'SBJ', '_', 'A1', 'A0', 'A0'],
                    [2, ',', ',', 1, 'P', '_', '_', '_', '_'],
                    [3, 'based', 'VBN', 1, 'APPO', 'base.01', '_', '_', '_'],
                    [4, 'in', 'IN', 3, 'LOC', '_', 'AM-LOC', '_', '_'],
                    [5, 'Los', 'NNP', 6, 'NAME', '_', '_', '_', '_'],
                    [6, 'Angeles', 'NNP', 4, 'PMOD', '_', '_', '_', '_'],
                    [7, ',', ',', 1, 'P', '_', '_', '_', '_'],
                    [8, 'makes', 'VBZ', 0, 'ROOT', 'make.01', '_', '_', '_'],
                    [9, 'and', 'CC', 8, 'COORD', '_', '_', '_', '_'],
                    [10, 'distributes', 'VBZ', 9, 'CONJ', 'distribute.01', '_', '_', '_'],
                    [11, 'electronic', 'JJ', 16, 'NMOD', '_', '_', '_', '_'],
                    [12, ',', ',', 11, 'P', '_', '_', '_', '_'],
                    [13, 'computer', 'NN', 11, 'COORD', '_', '_', '_', '_'],
                    [14, 'and', 'CC', 13, 'COORD', '_', '_', '_', '_'],
                    [15, 'building', 'NN', 14, 'CONJ', '_', '_', '_', '_'],
                    [16, 'products', 'NNS', 8, 'OBJ', '_', '_', 'A1', 'A1'],
                    [17, '.', '.', 8, 'P', '_', '_', '_', '_']]
        root = read_back_sentence(sentence)
        self.assertEqual(([0, 1, 1, 1, 1, 2, 2, 2, 3, 4, 7, 10, 10, 11, 13, 14, 15],
                          [0, 0, 1, 1, 0, 1, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0],
                          [('VBZ', 'makes'), ('NNP', 'Bell'), ('CC', 'and'), ('NNS', 'products'), ('.', '.'),
                           (',', ','), ('VBN', 'based'), (',', ','), ('VBZ', 'distributes'), ('JJ', 'electronic'),
                           ('IN', 'in'), (',', ','), ('NN', 'computer'), ('NNP', 'Angeles'), ('CC', 'and'),
                           ('NNP', 'Los'), ('NN', 'building')],
                          [1, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0],
                          [1, 1, 1, 0, 0, 0, 1, 0, 0, 1, 1, 0, 1, 0, 1, 0, 0],
                          [0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0]),
                         get_column_format(root))


if __name__ == '__main__':
    unittest.main()
