import argparse
import sys
from transition import transition_arc_eager, transition_arc_standard

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--standard', action='store_true', help='Choose the alternative arc-standard parsing')
parser.add_argument('-t', '--tab', action='store_true', help='Output in the tab format')
ARGS = parser.parse_args()

SH = 0; RE = 1; RA = 2; LA = 3

labels = ["nsubj", "csubj", "nsubjpass", "csubjpass", "dobj", "iobj", "ccomp", "xcomp", "nmod", "advcl", "advmod", "neg", "aux", "auxpass", "cop", "mark", "discourse", "vocative", "expl", "nummod", "acl", "amod", "appos", "det", "case", "compound", "mwe", "goeswith", "name", "foreign", "conj", "cc", "punct", "list", "parataxis", "remnant", "dislocated", "reparandum", "root", "dep", "nmod:npmod", "nmod:tmod", "nmod:poss", "acl:relcl", "cc:preconj", "compound:prt"]

def read_sentences():
    sentence = []
    sentences = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            sentences.append(sentence)
            sentence = []
        elif line[0] != "#":
            token = line.split("\t")
            sentence.append(token)
    return(sentences)

def attach_orphans(arcs, n):
    attached = []
    for (h, d, l) in arcs:
        attached.append(d)
    for i in range(1, n):
        if not i in attached:
            arcs.append((0, i, "root"))

def print_tab(arcs, words, tags):
    hs = {}
    ls = {}
    for (h, d, l) in arcs:
        hs[d] = h
        ls[d] = l
    for i in range(1, len(words)):
        print("\t".join([words[i], tags[i], str(hs[i]), ls[i]]))
    print()

def print_tree(root, arcs, words, indent):
    if root == 0:
        print(" ".join(words[1:]))
    children = [(root, i, l) for i in range(len(words)) for l in labels if (root, i, l) in arcs]
    for (h, d, l) in sorted(children):
        print(indent + l + "(" + words[h] + "_" + str(h) + ", " + words[d] + "_" + str(d) + ")")
        print_tree(d, arcs, words, indent + "  ")

def oracle_arc_eager(stack, buffer, heads, labels):
    stack_top = stack[-1]
    buf_1st = buffer[0]
    if heads[stack_top] == buf_1st:
        return (LA, labels[stack_top])
    if heads[buf_1st] == stack_top:
        return (RA, labels[buf_1st])

    buf_1st_dependents = [i for i, x in enumerate(heads) if x == buf_1st]
    if (buf_1st_dependents and min(buf_1st_dependents) < stack_top) or heads[buf_1st] < stack_top:
        return RE
    return SH

def oracle_arc_standard(stack, buffer, heads, labels, arcs):
    if len(stack) < 2:
        return SH
    stack_1st = stack[-1]
    stack_2nd = stack[-2]
    if heads[stack_2nd] == stack_1st:
        return (LA, labels[stack_2nd])
    if heads[stack_1st] == stack_2nd:
        dependents = [i for i, x in enumerate(heads) if x == stack_1st]
        all_dependent_arcs_build = True
        for d in dependents:
            if not (stack_1st, d, labels[d]) in arcs:
                all_dependent_arcs_build = False
                break
        if all_dependent_arcs_build:
            return (RA, labels[stack_1st])
    return SH

def parse(sentence):
    sentence.insert(0, ("root", "_", "0", "_"))
    words = [sentence[i][0] for i in range(len(sentence))]
    tags = [sentence[i][1] for i in range(len(sentence))]
    heads = [int(sentence[i][2]) for i in range(len(sentence))]
    labels = [sentence[i][3] for i in range(len(sentence))]
    stack = [0]
    buffer = [x for x in range(1, len(words))]
    arcs = []
    if ARGS.standard:
        while True:
            trans = oracle_arc_standard(stack, buffer, heads, labels, arcs)
            try:
                transition_arc_standard(trans, stack, buffer, arcs)
            except ValueError:
                print('Sentence is not projective!', file=sys.stderr)
                print(sentence, file=sys.stderr)
                break
            if not buffer and len(stack) == 1:
                break
    else:
        while buffer:
            trans = oracle_arc_eager(stack, buffer, heads, labels)
            transition_arc_eager(trans, stack, buffer, arcs)
    attach_orphans(arcs, len(words))
    if ARGS.tab:
        print_tab(arcs, words, tags)
    else:
        print_tree(0, arcs, words, "")

if __name__ == "__main__":
    for i, sentence in  enumerate(read_sentences()):
        parse(sentence)
