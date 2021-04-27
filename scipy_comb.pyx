# Copied from SciPy source code!!!

cdef unsigned long _comb_int_long(unsigned long N, unsigned long k):
    """
    Compute binom(N, k) for integers.
    """
    cdef unsigned long val, j, M, nterms

    if k > N:
        return 0

    M = N + 1
    nterms = min(k, N - k)

    val = 1

    for j in range(1, nterms + 1):
        val *= M - j
        val //= j

    return val

def _comb_int(int N, int k):
    # Fast path with machine integers
    try:
        r = _comb_int_long(N, k)
        if r != 0:
            return r
    except (OverflowError, TypeError):
        pass

    # Fallback
    N = int(N)
    k = int(k)

    if k > N or N < 0 or k < 0:
        return 0

    M = N + 1
    nterms = min(k, N - k)

    numerator = 1
    denominator = 1
    for j in range(1, nterms + 1):
        numerator *= M - j
        denominator *= j

    return numerator // denominator

