"""Bit-twiddling helpers in bitsnbobs, snoob, and scipycomb."""

import math
from itertools import combinations

import pytest

from mtrip import snoob, triplet_omp
from mtrip.bitsnbobs import (
    get_binary_subsets,
    init_bipart_rep_function,
    popcount,
    replace_2_with_k,
)
from mtrip.scipycomb import _comb_int


@pytest.mark.parametrize("x", [0, 1, 2, 3, 0b1011, 2**20 - 1, 2**31])
def test_popcount(x):
    assert popcount(x) == bin(x).count("1")


@pytest.mark.parametrize("n", [0b1, 0b1011, 0b110110])
def test_get_binary_subsets(n):
    expected = {s for s in range(1, n) if s & n == s}
    result = get_binary_subsets(n)
    assert len(result) == len(set(result))
    assert set(result) == expected
    assert set(get_binary_subsets(n, include_self=True)) == expected | {n}
    assert set(get_binary_subsets(n, include_empty_set=True)) == expected | {0}


def test_get_binary_subsets_of_empty_set():
    assert get_binary_subsets(0, include_self=True, include_empty_set=True) == [0]


@pytest.mark.parametrize("universe", [0b11111, 0b1011010110, 2**12 - 1])
def test_get_all_snoobs(universe):
    bits = [i for i in range(universe.bit_length()) if universe >> i & 1]
    for k in range(1, len(bits) + 1):
        expected = sorted(sum(1 << i for i in c) for c in combinations(bits, k))
        assert snoob.get_all_snoobs(universe, k) == expected


@pytest.mark.parametrize(("n", "k"), [(0, 0), (5, 2), (12, 6), (20, 3), (3, 5)])
def test_comb_int(n, k):
    assert _comb_int(n, k) == math.comb(n, k)


def test_replace_2_with_k():
    for x in range(2**8):
        digits = [i for i in range(8) if x >> i & 1]
        assert replace_2_with_k(x, 3) == sum(3**i for i in digits)


def test_bipart_rep_matches_c_lookup_table():
    n = 7
    two2three = triplet_omp.create_two2three(n)
    rep = init_bipart_rep_function(n)
    for x in range(2**n):
        assert two2three[x] == replace_2_with_k(x, 3)
    seen = {}
    for a in range(2**n):
        for b in get_binary_subsets(2**n - 1 - a, include_empty_set=True):
            r = rep(a, b)
            assert r == rep(b, a)
            assert r == min(
                two2three[a] + 2 * two2three[b], 2 * two2three[a] + two2three[b]
            )
            # Distinct unordered bipartitions get distinct indices.
            assert seen.setdefault(r, frozenset((a, b))) == frozenset((a, b))
