cdef extern from "scores_omp.h":
    int combinations_2(int n)
cdef extern from "scores_omp.h" nogil:
    void fill_compressed_score_representation(
            int *left_sets,
            int *right_sets,
            int *weights,
            int n_biparts,
            int n_species,
            int *scores,
            int *two2three,
            )
#    void get_optimal_bipart(int full_set, int *left, int *right, int *scores, 
#            int *two2three)
cdef extern from "lookup_table.h":
    void fill_two2three(int *two2three, int n)

import numpy as np

def py_combinations_2(n):
    return combinations_2(n)

def create_two2three(n):
    ar = np.zeros(2**n, dtype=np.intc)
    if not ar.flags['C_CONTIGUOUS']:
        ar = np.ascontiguousarray(ar)

    cdef int[::1] ar_memview = ar

    fill_two2three(&ar_memview[0], n)

    return ar

def py_compressed_score_rep(weights, n_species):
    n_biparts = len(weights)
    ls = np.zeros(n_biparts, dtype=np.intc)
    rs = np.zeros(n_biparts, dtype=np.intc)
    ws = np.zeros(n_biparts, dtype=np.intc)

    for (i, ((l,r),w)) in enumerate(weights.items()):
        ls[i]=l
        rs[i]=r
        ws[i]=w

    two2three = create_two2three(n_species)

    scores = np.zeros(2*3**(n_species-1), dtype=np.intc)
    
    arrays_to_c = [ls, rs, ws, scores]
    for ar in [ls, rs, ws, scores]:
        if not ar.flags['C_CONTIGUOUS']:
            ar = np.ascontiguousarray(ar)

    cdef int[::1] scores_memview = scores
    cdef int[::1] two2three_memview = two2three
    cdef int[::1] ls_memview = ls
    cdef int[::1] rs_memview = rs
    cdef int[::1] ws_memview = ws

    fill_compressed_score_representation(
            &ls_memview[0],
            &rs_memview[0],
            &ws_memview[0], 
            n_biparts,
            n_species,
            &scores_memview[0],
            &two2three_memview[0],
            )

    return scores

#def optimal_bipart(int input_set, scores, two2three):
#    cdef int[::1] scores_memview = scores
#    cdef int[::1] two2three_memview = two2three
#    cdef int left
#    cdef int right
#    get_optimal_bipart(
#            input_set,
#            &left,
#            &right,
#            &scores_memview[0],
#            &two2three_memview[0]
#            )
#
#    return left, right
