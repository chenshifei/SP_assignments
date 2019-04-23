from sys import stdin, stderr
from json import loads, dumps

def cnf(tree):
    # CODE REMOVED

    # MASTERS: INSERT YOUR CODE HERE!

    # BACHELORS: CODE ONLY NEEDED FOR ONE OF THE POSSIBLE VG TASKS
    if len(tree) == 2:
        if isinstance(tree[1], str):
            return tree
        root = tree[0] + '+' + tree[1][0]
        return cnf([root] + tree[1][1:])
    if len(tree) > 3:
        root = tree[0] + '|' + tree[1][0]
        return cnf([tree[0], tree[1], [root] + tree[2:]])
    return [tree[0], cnf(tree[1]), cnf(tree[2])]

def is_cnf(tree):
    n = len(tree)
    if n == 2:
        return isinstance(tree[1], str)
    elif n == 3:
        return is_cnf(tree[1]) and is_cnf(tree[2])
    else:
        return False

def words(tree):
    if isinstance(tree, str):
        return [tree]
    else:
        ws = []
        for t in tree[1:]:
            ws = ws + words(t)
        return ws

if __name__ == "__main__":

    for line in stdin:
        tree = loads(line)
        sentence = words(tree)
        input = str(dumps(tree))
        tree = cnf(tree)
        if is_cnf(tree) and words(tree) == sentence:
            print(dumps(tree))
        else:
            print("Something went wrong!", file=stderr)
            print("Sentence: " + " ".join(sentence), file=stderr)
            print("Input: " + input, file=stderr)
            print("Output: " + str(dumps(tree)), file=stderr)
            exit()


