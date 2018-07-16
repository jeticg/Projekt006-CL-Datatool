import unittest
from analysis.process_conll08 import parse_conll08, export_to_table


class TestParse(unittest.TestCase):
    def test_parse(self):
        with open('../support/sampleDepTree.txt') as file:
            forest = parse_conll08('../data/pb_frames', file)
        correct = [[1, 'Ms.', 'NNP', 2, 'TITLE', '_', '_'],
                   [2, 'Haag', 'NNP', 3, 'SBJ', '_', 'A0'],
                   [3, 'plays', 'VBZ', 0, 'ROOT', 'play.02', '_'],
                   [4, 'Elianti', 'NNP', 3, 'OBJ', '_', 'A1'],
                   [5, '.', '.', 3, 'P', '_', '_']]
        self.assertEqual(export_to_table(forest[1]), correct)


if __name__ == '__main__':
    unittest.main()
