# distutils: language = c
# cython: language_level=3

from libc.stdlib cimport malloc, free

def _comb_int(N, k):
    """
    Compute n choose k where n and k are integers.
    """
    if k > N or k < 0:
        return 0

    if k == 0 or k == N:
        return 1

    if k > N // 2:
        k = N - k

    res = 1
    
    for i in range(k):
        res = (res * (N - i)) // (i + 1)
    
    return res