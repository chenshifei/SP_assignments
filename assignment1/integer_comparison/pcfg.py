from sys import argv, stderr

from os.path import exists
#from __future__ import division
from collections import Counter, defaultdict
from json import loads, dumps
from time import time
#from stat_parser.word_classes import word_class


class PCFG:
    RARE_WORD_COUNT = 5
    if __debug__:
        RARE_WORD_COUNT = 0

    def __init__(self):
        self._sym_count = Counter()
        self._unary_count = Counter()
        self._binary_count = Counter()
        self._words_count = Counter()
        self.q1 = defaultdict(float)
        self.q2 = defaultdict(float)
        self.q3 = defaultdict(float)
        self.well_known_words = []
        self.N = []
        self.__N_set = set()
        self.binary_rules = defaultdict(list)
        self.unary_rules = defaultdict(list)

    def norm_word(self, word):
        return word if word in self.well_known_words else "_RARE_" #word_class(word)

    def __build_caches(self):
        for x, y1, y2 in self.q2.keys():
            self.binary_rules[x].append((y1, y2))

        for x, y1 in self.q3.keys():
            self.unary_rules[x].append((y1))


    def learn_from_treebank(self, treebank):
        for s in open(treebank):
            self.count(loads(s))

        # Words
        for word, count in self._words_count.items():
            if count >= PCFG.RARE_WORD_COUNT:
                self.well_known_words.append(word)
        self.well_known_words = sorted(self.well_known_words)

        # Normalise the unary rules count
        norm = Counter()
        for (x, word), count in self._unary_count.items():
            norm[(x, self.norm_word(word))] += count
        self._unary_count = norm

        # Q1
        for (x, word), count in self._unary_count.items():
            x_idx = self.N.index(x)
            w_idx = self.well_known_words.index(word)
            self.q1[x_idx, w_idx] = self._unary_count[x, word] / self._sym_count[x]

        # Q2
        for (x, y1, y2), count in self._binary_count.items():
            x_idx = self.N.index(x)
            y1_idx = self.N.index(y1)
            y2_idx = self.N.index(y2)
            self.q2[x_idx, y1_idx, y2_idx] = self._binary_count[x, y1, y2] / self._sym_count[x]

        # Q3 currently not handled

        self.__build_caches()

    def count(self, tree):
        # Base case: terminal symbol
        if isinstance(tree, str):
            return

        # Count the non-terminal symbols
        sym = tree[0]
        self._sym_count[sym] += 1
        self.__N_set.add(sym)

        if len(tree) == 3:
            # Binary Rule
            y1, y2 = (tree[1][0], tree[2][0])
            self._binary_count[(sym, y1, y2)] += 1
            self.__N_set.update(set([y1, y2]))

            # Recursively count the children
            self.count(tree[1])
            self.count(tree[2])

        elif len(tree) == 2:
            # Unary Rule
            word = tree[1]
            self._unary_count[(sym, word)] += 1
            self._words_count[word] += 1

        self.N = sorted(self.__N_set)

    def save_model(self, path):
        with open(path, 'w') as model:
            for (x, word), p in self.q1.items():
                model.write(dumps(['Q1', x, word, p]) + '\n')

            for (x, y1, y2), p in self.q2.items():
                model.write(dumps(['Q2', x, y1, y2, p]) + '\n')

            # Q3 currently not handled

            model.write(dumps(['N', self.N]) + '\n')

            model.write(dumps(['WORDS', list(self.well_known_words)]) + '\n')


    def load_model(self, path):
        with open(path) as model:
            for line in model:
                data = loads(line)
                if data[0] == 'Q1':
                    _, x, word, p = data
                    self.q1[x, word] = p

                elif data[0] == 'Q2':
                    _, x, y1, y2, p = data
                    self.q2[x, y1, y2] = p

                elif data[0] == 'Q3':
                    _, x, y1, p = data
                    self.q3[x, y1] = p

                elif data[0] == 'N':
                    self.N = data[1]

                elif data[0] == 'WORDS':
                    self.well_known_words = data[1]

        self.__build_caches()


if __name__ == "__main__":

    if len(argv) != 3:
        print("usage: python3 pcfg.py TREEBANK GRAMMAR")
        exit()

    treebank_file = argv[1]
    grammar_file = argv[2]

    start = time()
    print("Extracting grammar from " + treebank_file + " ...", file=stderr)
    pcfg = PCFG()
    pcfg.learn_from_treebank(treebank_file)
    print("Saving grammar to " + grammar_file + " ...", file=stderr)
    pcfg.save_model(grammar_file)
    print("Time: %.2fs\n" % (time() - start), file=stderr)
