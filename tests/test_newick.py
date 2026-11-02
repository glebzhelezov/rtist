"""Newick parsing and bipartition extraction."""

import pytest

import mtrip.median_tree_reconstruction as mtr


def test_simplify_strips_lengths_labels_and_semicolon():
    s = "((A:0.1,B:2)ab:0.5, C:1.25)root;"
    assert mtr.simplify_nwk(s) == "((A,B),C)"


@pytest.mark.parametrize(
    "length", ["1e-06", "2.5E-3", "1.0e+2", "-0.1", "3.", ".5", "1", ""]
)
def test_simplify_strips_any_branch_length(length):
    """Branch lengths in any number format (IQ-TREE and RAxML write 1e-06)."""
    s = f"((A:{length},B:{length})90:{length},C:{length}):{length};"
    assert mtr.simplify_nwk(s) == "((A,B),C)"


def test_get_names_is_sorted_and_consistent():
    names, dictionary, reverse = mtr.get_names(["((C,A),B)", "((D,A),B)"])
    assert reverse == ["A", "B", "C", "D"]
    assert dictionary == {"A": 0, "B": 1, "C": 2, "D": 3}
    assert names == set(reverse)


def test_unlabeled_tip_is_an_error():
    with pytest.raises(SyntaxError, match="line 2"):
        mtr.get_names(["((A,B),C)", "((A,),C)"])


def test_splitter():
    assert mtr.splitter("((A,B),(C,D))") == ("(A,B)", "(C,D)")
    assert mtr.splitter("A") == ("A",)


def test_get_biparts():
    dictionary = {"A": 0, "B": 1, "C": 2, "D": 3}
    biparts = mtr.get_biparts("((A,B),(C,D))", dictionary)
    # Each internal node gives (smaller, larger) bitmasks of its two sides.
    assert sorted(biparts) == sorted(
        [(0b0001, 0b0010), (0b0100, 0b1000), (0b0011, 0b1100)]
    )


def test_get_weights_counts_repeated_bipartitions():
    dictionary = {"A": 0, "B": 1, "C": 2}
    weights = mtr.get_weights(["((A,B),C)", "((A,B),C)", "((A,C),B)"], dictionary)
    assert weights[(0b001, 0b010)] == 2
    assert weights[(0b011, 0b100)] == 2
    assert weights[(0b001, 0b100)] == 1
    assert weights[(0b010, 0b101)] == 1
