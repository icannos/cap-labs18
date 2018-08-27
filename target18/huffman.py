#!/usr/bin/env python3

# Generate a Huffman code given a set of data and weights associated.

# The data come from the standard input, with the format:
# `[id] [item] [weight]` in every lines.
# - [id] is an integer associated to every item.
# - [item] is a string characterising a data element
# - [weight] is an integer giving the weight of the item.
# The input must end with EOF.
# The ids may be given in the ascendant order, starting from 0.

# The encoding is printed in the standard output.
# The first line contains the maximal length of the longer generated code.
# Then, each of the following line contains:
# [item] [id] [len] [code]
# where [code] is a string composed by 0 and 1 associated with an item. [len]
# is the length of [code]. [id] and [item] are the same as explained earlier.

# In this algorithm, binary trees are used to calculate the Huffman encoding.
# A binary tree is represented either by:
# - An integer, representing the id of an item (the tree is a leaf).
# - A 2-uple (l, r) with l and r two trees

def balanced_tree(ids):
    """Given a list of ids, create a balanced binary tree.

    For each node, the difference in the number of leafs between the right son
    and the left son is at most 1.
    """
    if len(ids) == 1:
        return ids[0]

    m = len(ids) // 2
    return (balanced_tree(ids[:m]), balanced_tree(ids[m:]))

def huffman_tree(weights):
    """Return a binary tree given a list of weights."""
    leafs = [(w, i) for (i, w) in enumerate(weights)]

    # Isolating the 0-weight ids.
    zero_ids = [i for (w, i) in leafs if w == 0]
    subtrees = [(w, i) for (w, i) in leafs if w != 0]
    if zero_ids != []:
        # If there are 0-weight ids, a balanced tree is created for those ids
        # so that the final tree is as balanced as possible, while remaining
        # optimal.
        subtrees.append((0, balanced_tree(zero_ids)))

    while len(subtrees) > 1:
        subtrees.sort(key=lambda c: c[0], reverse=True)
        wr, right = subtrees.pop()
        wl, left = subtrees.pop()
        subtrees.append((wl + wr, (left, right)))

    [(w, t)] = subtrees
    return t

def huffman_codes(tree, prefix, codes):
    """Given a Huffman tree `tree`, compute all the codes of the ids in the
    tree, starting with the string `prefix`. These codes are stored in the
    list `codes`."""
    if isinstance(tree, int):
        codes[tree] = prefix
    else:
        left, right = tree
        huffman_codes(left, prefix + "0", codes)
        huffman_codes(right, prefix + "1", codes)

if __name__ == "__main__":
    items = []
    nb_exec = []
    
    i = 0
    try:
        while True:
            tokens = input().split()
            assert len(tokens) == 3
            assert int(tokens[0]) == i
            items.append(tokens[1])
            nb_exec.append(int(tokens[2]))
            i += 1
    except EOFError:
        pass

    tree = huffman_tree(nb_exec)
    codes = [None] * len(items)
    huffman_codes(tree, "", codes)

    print(max([len(c) for c in codes]))
    for (i, c) in enumerate(codes):
        print(items[i], i, len(c), c)
        
    print("pop", "None", len(codes[9])+2, codes[9]+"01") 
