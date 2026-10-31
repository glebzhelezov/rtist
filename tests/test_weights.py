"""The C core: triplet counting and the expanded bipartition weights."""

from random import Random

import pytest
from brute import bipartition_triplets, random_gene_trees

import mtrip.median_tree_reconstruction as mtr
from mtrip import triplet_omp
from mtrip.bitsnbobs import get_binary_subsets, init_bipart_rep_function


@pytest.mark.parametrize("n", range(8))
def test_combinations_2(n):
    assert triplet_omp.py_combinations_2(n) == n * (n - 1) // 2


def test_n_common_triplets_against_definition():
    rng = Random(0)
    n = 8
    for _ in range(2000):
        labels = [rng.randrange(3) for _ in range(n)]  # 0: a, 1: b, 2: outside
        a = sum(1 << i for i in range(n) if labels[i] == 0)
        b = sum(1 << i for i in range(n) if labels[i] == 1)
        labels = [rng.randrange(3) for _ in range(n)]
        c = sum(1 << i for i in range(n) if labels[i] == 0)
        d = sum(1 << i for i in range(n) if labels[i] == 1)
        expected = len(bipartition_triplets(a, b) & bipartition_triplets(c, d))
        assert triplet_omp.py_n_common_triplets(a, b, c, d) == expected


@pytest.mark.parametrize(("seed", "taxa"), [(1, "ABCDE"), (2, "ABCDEFG")])
def test_expanded_weights_against_definition(seed, taxa):
    """weights[(x, y)] = sum over observed bipartitions (c, d) of
    w(c, d) * n_common_triplets(x, y, c, d), for every disjoint x, y."""
    nwks = random_gene_trees(seed, n_trees=30, taxa=taxa, min_taxa=3)
    triplet_weights, dictionary, _ = mtr.process_nwks(nwks, n_threads=2)
    n = len(dictionary)
    observed = mtr.get_weights([mtr.simplify_nwk(s) for s in nwks], dictionary)
    rep = init_bipart_rep_function(n)

    universe = 2**n - 1
    for subset in get_binary_subsets(universe, include_self=True):
        for x in get_binary_subsets(subset):
            y = subset - x
            expected = sum(
                w * triplet_omp.py_n_common_triplets(x, y, c, d)
                for (c, d), w in observed.items()
            )
            assert triplet_weights[rep(x, y)] == expected, (x, y)
