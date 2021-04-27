# Wrapper to access the popcount function provided by gcc
cdef extern:
    int __builtin_popcount(unsigned int) nogil
    int __builtin_ctz (unsigned int x) nogil


def popcount(unsigned int n):
    """Wrapper to access the popcount function provided by gcc."""
    return __builtin_popcount(n)

def bit_scan1(unsigned int n):
    #return __builtin_ffs(n)
    if n == 0:
        return -1
    return __builtin_ctz(n)


#Algorithm by Bill Gosper
### https://www.chessprogramming.org/Traversing_Subsets_of_a_Set
cdef unsigned int snoob(unsigned int sub, unsigned int universe):
    """Next largest number with the the same number of bits, with bits only where universe has bits"""
    cdef unsigned int tmp = sub - 1
    cdef unsigned int rip = universe & (tmp + (sub & (0 - sub)) - universe)
    
    sub = (tmp & sub) ^ rip
    sub &= sub-1
    
    #print(tmp, rip, sub)

    while sub > 0:
        tmp = universe & (0-universe)
        rip ^= tmp
        universe ^= tmp
        sub &= sub-1

    return rip

def pysnoob(unsigned int sub, unsigned int universe):
    return snoob(sub, universe)


def get_binary_subsets(unsigned int n, include_self=False, include_empty_set=False):
    """Generate a list of all numbers with set bits only where n has set bits, excluding n.
    
    If we assume n represents a set (ith bit denoting membership),
    then these are all proper non-empty subsets.
    
    input:
    --------
    n - integer
    include_self=False - set to True if output should include n (i.e. by default only proper
                subsets are outputted.)
    include_empty_set=False - set to True if output should include empty set (i.e. 0)

    If n=0, include_self=True, and include_empty_set=True, then [0] is returned.
    
    output:
    --------
    subsets - list of integers, each denoting a subset.
    
    """
    subsets = []
    cdef unsigned int i = n

    if include_self:
        subsets.append(i)

    i = n & (i - 1)

    while i > 0:
        subsets.append(i)
        i = n & (i - 1)

    if include_empty_set:
        # Don't include 0 twice
        if not (include_self and n==0):
            subsets.append(0)

    return subsets


def replace_2_with_k(unsigned int x, int n):
    """Take 2^n_0 + ... 2^n_k and return k^n_0 + ... 2^n_k"""
    cdef int result = 0

    cdef int set_bit_position = bit_scan1(x)

    while set_bit_position != -1:
        result += n ** set_bit_position
        x ^= (1 << set_bit_position)
        set_bit_position = bit_scan1(x)

    return result


def init_bipart_rep_function(n_species):
    """Initializes a function which transforms a binary-represented 
    bipartition into a base-3 number."""
    to_1 = [replace_2_with_k(x, 3) for x in range(2 ** n_species - 1 + 1)]
    to_2 = [2 * x for x in to_1]

    def get_bipart_rep(a, b):
        """Does not check if this makes sense"""
        rep = min(to_1[a] + to_2[b], to_1[b] + to_2[a])
        return rep

    return get_bipart_rep


