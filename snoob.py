from bitsnbobs import popcount, pysnoob
from scipycomb import _comb_int as comb
#from scipy.special import comb

def get_first_n_combo(x, n):
    """First number with n set bits, which only has set bits where x has set bits."""
    if popcount(x) < n:
        print('Popcount of x is too small!')
        return -1
    
    t = x
    for _ in range(n):
        t ^= t&(-t)
    return x^t


def get_all_snoobs(x, n_set_bits):
    """Get all integers with n_bits set bits. Each set bit must be present in x's binary representation."""
    # number of set bits in x
    n_universe_bits = popcount(x)
    # the length our output should have
    n_combos = comb(n_universe_bits, n_set_bits)
    
    combos = []
    # The first such combo.
    combo = get_first_n_combo(x, n_set_bits)
    for _ in range(n_combos):
        combos.append(combo)
        #print(combo, ' = ', bin(combo), ' has popcount ', popcount(combo))
        combo = pysnoob(combo, x)
    
    return combos


def binary_with_padding(x, padding=8):
    "Return binary representation of x with padding."
    s = bin(x)[2:]
    padding = max(padding, len(s))
    return (padding-len(s))*'0'+s
