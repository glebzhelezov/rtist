"""End-to-end: mtrip's median trees against an exhaustive search."""

import pytest
from brute import (
    brute_force_median,
    clusters,
    parse_newick,
    random_gene_trees,
)
from common import EXAMPLES, read_nwks

from mtrip.median_tree_reconstruction import median_triplet_trees


def run_mtrip(nwks, n_threads=1):
    trees, reverse_dictionary, _, stack, _ = median_triplet_trees(
        nwks, n_threads=n_threads, return_extra=True
    )
    score = stack[2 ** len(reverse_dictionary) - 1]
    return score, trees


def assert_matches_brute_force(nwks, n_threads=1):
    score, trees = run_mtrip(nwks, n_threads=n_threads)
    tree_clusters = [clusters(parse_newick(t)) for t in trees]
    best, optimal = brute_force_median(nwks)

    assert score == best
    assert len(tree_clusters) == len(set(tree_clusters)), "duplicate trees"
    assert set(tree_clusters) == optimal
    return score, len(trees)


@pytest.mark.parametrize(
    ("name", "score", "n_trees"),
    [
        ("example", 1, 3),  # three conflicting triplets: a three-way tie
        ("example_5tips", 26, 2),
        ("large_example", 65, 28),  # some gene trees lack F or G
    ],
)
def test_examples(name, score, n_trees):
    nwks = read_nwks(EXAMPLES / f"{name}.nwk")
    assert assert_matches_brute_force(nwks) == (score, n_trees)


@pytest.mark.parametrize("seed", range(6))
def test_random_inputs_with_missing_taxa(seed):
    nwks = random_gene_trees(seed, n_trees=25, taxa="ABCDEF", min_taxa=3)
    assert_matches_brute_force(nwks)


def test_seven_taxa_many_trees():
    nwks = random_gene_trees(100, n_trees=60, taxa="ABCDEFG", min_taxa=4)
    assert_matches_brute_force(nwks, n_threads=4)


def test_thread_count_does_not_change_result():
    nwks = random_gene_trees(7, n_trees=200, taxa="ABCDEFGHIJ", min_taxa=6)
    assert run_mtrip(nwks, n_threads=1) == run_mtrip(nwks, n_threads=4)
