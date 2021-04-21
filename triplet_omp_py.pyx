cdef extern from "weights_omp.h":
    int combinations_2(int n)
cdef extern from "weights_omp.h" nogil:
    void fill_compressed_weight_representation(
            int *left_sets,
            int *right_sets,
            int *bipart_weights,
            int n_biparts,
            int n_species,
            int *weights,
            int *two2three,
            int n_threads,
            )
#    void get_optimal_bipart(int full_set, int *left, int *right, int *weights, 
#            int *two2three)
cdef extern from "lookup_table.h":
    void fill_two2three(int *two2three, int n)

import numpy as np

def py_combinations_2(n):
    """Return n choose 2."""
    return combinations_2(n)

def create_two2three(n):
    """Create an array whose ith element is the number i, with 3^n instead
    of 2^n in the binary expansion of."""

    ar = np.zeros(2**n, dtype=np.intc)
    if not ar.flags['C_CONTIGUOUS']:
        ar = np.ascontiguousarray(ar)

    cdef int[::1] ar_memview = ar

    fill_two2three(&ar_memview[0], n)

    return ar

def py_compressed_weight_rep(bipart_weights, n_species, n_threads=8):
    """Computes the compressed representation of the bipartition weights."""
    n_biparts = len(bipart_weights)
    ls = np.zeros(n_biparts, dtype=np.intc)
    rs = np.zeros(n_biparts, dtype=np.intc)
    ws = np.zeros(n_biparts, dtype=np.intc)

    for (i, ((l,r),w)) in enumerate(bipart_weights.items()):
        ls[i]=l
        rs[i]=r
        ws[i]=w

    two2three = create_two2three(n_species)

    weights = np.zeros(2*3**(n_species-1), dtype=np.intc)
    
    arrays_to_c = [ls, rs, ws, weights]
    for ar in [ls, rs, ws, weights]:
        if not ar.flags['C_CONTIGUOUS']:
            ar = np.ascontiguousarray(ar)

    cdef int[::1] weights_memview = weights
    cdef int[::1] two2three_memview = two2three
    cdef int[::1] ls_memview = ls
    cdef int[::1] rs_memview = rs
    cdef int[::1] ws_memview = ws

    fill_compressed_weight_representation(
            &ls_memview[0],
            &rs_memview[0],
            &ws_memview[0], 
            n_biparts,
            n_species,
            &weights_memview[0],
            &two2three_memview[0],
            n_threads,
            )

    return weights
