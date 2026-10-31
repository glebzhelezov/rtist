"""Brute-force reference implementations, independent of mtrip's code.

Trees are nested tuples of leaf names, e.g. (("A", "B"), "C").
"""

from collections import Counter
from itertools import combinations
from random import Random


def parse_newick(s):
    """Parse a plain rooted Newick string (leaf names only) into nested tuples."""
    s = s.strip().rstrip(";")
    pos = 0

    def node():
        nonlocal pos
        if s[pos] == "(":
            pos += 1
            children = [node()]
            while s[pos] == ",":
                pos += 1
                children.append(node())
            assert s[pos] == ")", s
            pos += 1
            return tuple(children)
        start = pos
        while pos < len(s) and s[pos] not in ",()":
            pos += 1
        return s[start:pos]

    tree = node()
    assert pos == len(s), s
    return tree


def leaves(tree):
    if isinstance(tree, str):
        return frozenset([tree])
    return frozenset().union(*(leaves(t) for t in tree))


def clusters(tree):
    """All clusters (leaf sets of subtrees), as a frozenset. Identifies the tree."""
    out = set()

    def walk(t):
        c = leaves(t)
        out.add(c)
        if not isinstance(t, str):
            for child in t:
                walk(child)

    walk(tree)
    return frozenset(out)


def triplets(tree):
    """Map each 3-leaf set to the pair that the tree groups together."""
    taxa = leaves(tree)
    resolved = {}
    for c in clusters(tree):
        outside = taxa - c
        for pair in combinations(sorted(c), 2):
            for z in outside:
                resolved[frozenset((*pair, z))] = frozenset(pair)
    return resolved


def all_rooted_binary_trees(taxa):
    """Every rooted binary tree on taxa, by inserting leaves into every edge."""
    taxa = sorted(taxa)
    trees = [taxa[0]]
    for leaf in taxa[1:]:
        new = []
        for t in trees:
            new.extend(_insert_everywhere(t, leaf))
        trees = new
    return trees


def _insert_everywhere(t, leaf):
    yield (t, leaf)
    if not isinstance(t, str):
        a, b = t
        for a2 in _insert_everywhere(a, leaf):
            yield (a2, b)
        for b2 in _insert_everywhere(b, leaf):
            yield (a, b2)


def brute_force_median(nwks):
    """Return (best score, set of optimal trees as cluster sets).

    The score of a species tree is the number of (gene tree, triplet) pairs
    on which it agrees with the gene tree, using each gene tree's own taxa.
    """
    gene_trees = [parse_newick(s) for s in nwks]
    taxa = frozenset().union(*(leaves(g) for g in gene_trees))
    observed = Counter()
    for g in gene_trees:
        observed.update(triplets(g).items())

    best, optimal = -1, set()
    for t in all_rooted_binary_trees(taxa):
        score = sum(observed[item] for item in triplets(t).items())
        if score > best:
            best, optimal = score, {clusters(t)}
        elif score == best:
            optimal.add(clusters(t))
    return best, optimal


def random_gene_trees(seed, n_trees, taxa, min_taxa):
    """Seeded random rooted binary trees; each uses a random subset of taxa."""
    rng = Random(seed)
    out = []
    for _ in range(n_trees):
        nodes = rng.sample(list(taxa), rng.randint(min_taxa, len(taxa)))
        while len(nodes) > 1:
            a = nodes.pop(rng.randrange(len(nodes)))
            b = nodes.pop(rng.randrange(len(nodes)))
            nodes.append(f"({a},{b})")
        out.append(nodes[0] + ";")
    return out


def bipartition_triplets(a, b):
    """Triplets displayed by bipartition (a, b), as (pair, third) bit positions."""

    def bits(x):
        return [i for i in range(x.bit_length()) if x >> i & 1]

    out = set()
    for side, other in ((a, b), (b, a)):
        for pair in combinations(bits(side), 2):
            for z in bits(other):
                out.add((pair, z))
    return out
