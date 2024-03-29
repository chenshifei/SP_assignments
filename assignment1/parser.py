"""
CKY algorithm from the "Natural Language Processing" course by Michael Collins
https://class.coursera.org/nlangp-001/class
"""
import sys
import operator
from sys import stdin, stderr
from time import time
from json import dumps
from multiprocessing import Pool

from collections import defaultdict
from pprint import pprint

from pcfg import PCFG
from tokenizer import PennTreebankTokenizer

def argmax(lst):
    return max(lst) if lst else (0.0, None)

def backtrace(back, bp):
    # ADD YOUR CODE HERE
    # Extract the tree from the backpointers
    if len(back) == 3:
        (c, c1), start, end = back
        return [c, c1]
    else:
        (c, c1, c2), start, mid, end = back
        return [c, backtrace(bp[start][mid][c1], bp), backtrace(bp[mid][end][c2], bp)]

def CKY(pcfg, norm_words):
    # ADD YOUR CODE HERE
    # IMPLEMENT CKY

    # NOTE: norm_words is a list of pairs (norm, word), where word is the word
    #       occurring in the input sentence and norm is either the same word,
    #       if it is a known word according to the grammar, or the string _RARE_.
    #       Thus, norm should be used for grammar lookup but word should be used
    #       in the output tree.

    # Initialize your charts (for scores and backpointers)

    n = len(norm_words)
    scores = [[defaultdict(float) for i in range(n + 1)] for j in range(n)]
    backpointers = [[defaultdict(tuple) for i in range(n + 1)] for j in range(n)]

    # Code for adding the words to the chart

    for i, (norm, word) in enumerate(norm_words):
        for (c, w), p in pcfg.q1.items():
            if w == norm:
                scores[i][i + 1][c] = p
                backpointers[i][i + 1][c] = ((c, word), i, i + 1)

    # Code for the dynamic programming part, where larger and larger subtrees are built

    sym_list = pcfg.binary_rules.keys()
    for end in range(2, n + 1):
        for start in range(end - 2, -1, -1):
            for sym in sym_list:
                best = 0
                bp = None
                for y1, y2 in pcfg.binary_rules[sym]:
                    for mid in range(start + 1, end):
                        cell1 = scores[start][mid]
                        cell2 = scores[mid][end]
                        if not cell1.get(y1) or not cell2.get(y2):
                            continue
                        t1 = cell1[y1]
                        t2 = cell2[y2]
                        p = pcfg.q2[(sym, y1, y2)]
                        candidate = t1 * t2 * p
                        if best < candidate:
                            best = candidate
                            bp = ((sym, y1, y2), start, mid, end)
                backpointers[start][end][sym] = bp
                scores[start][end][sym] = best

    # Below is one option for retrieving the best trees,
    # assuming we only want trees with the "S" category
    # This is a simplification, since not all sentences are of the category "S"
    # The exact arguments also depends on how you implement your back-pointer chart.
    # Below it is also assumed that it is called "bp"
    # return backtrace(bp[0, n, "S"], bp)

    possible_roots = scores[0][n]
    root = 'S'
    root = max(possible_roots.items(), key=operator.itemgetter(1))[0]
    tree = backtrace(backpointers[0][n][root], backpointers)
    return tree

class Parser:
    def __init__(self, pcfg):
        self.pcfg = pcfg
        self.tokenizer = PennTreebankTokenizer()

    def parse(self, sentence):
        words = self.tokenizer.tokenize(sentence)
        norm_words = []
        for word in words:                # rare words normalization + keep word
            norm_words.append((self.pcfg.norm_word(word), word))
        tree = CKY(self.pcfg, norm_words)
        tree[0] = tree[0].split("|")[0]
        return tree

def display_tree(tree):
    pprint(tree)

def do_parse_task(seqno, sentence):
    parsing_start = time()
    tree = parser.parse(sentence)
    # Keep seqno as a reference number in case the task order is arbitrary
    # This happens when multithreading the tasks. eval.py couldn't handle
    # if the line numbers in the prediction file and the golden file don't match
    print(dumps({seqno: tree}), flush=True)
    print('Seq {} parsing time: {:.2f}s'.format(seqno, time() - parsing_start), file=stderr)

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("usage: python3 parser.py GRAMMAR")
        exit()

    start = time()
    grammar_file = sys.argv[1]
    print("Loading grammar from " + grammar_file + " ...", file=stderr)
    pcfg = PCFG()
    pcfg.load_model(grammar_file)
    parser = Parser(pcfg)

    print("Parsing sentences ...", file=stderr)

    if __debug__:
        for i, sentence in enumerate(stdin):
            do_parse_task(i, sentence)
    else:
        with Pool(4) as pool:
            pool.starmap(do_parse_task, enumerate(stdin))

    print("Time: (%.2f)s\n" % (time() - start), file=stderr)
