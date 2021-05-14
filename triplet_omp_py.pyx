from cpython cimport array
import array

IF HAVE_CYSIGNALS:
    from cysignals.signals cimport sig_on, sig_off
ELSE:
    # for non-POSIX systems
    noop = lambda: None
    sig_on = noop
    sig_off = noop

cdef extern from "weights_omp.h":
    int combinations_2(int n)
    int n_common_triplets(int a, int b, int c, int d)
cdef extern from "weights_omp.h" nogil:
    void fill_compressed_weight_representation(
        int *subsets,
        int *start_i,
        int *end_i,
        int *left_sets,
        int *right_sets,
        int *bipart_weights,
        int n_subsets,
        int n_species,
        int *weights,
        int *two2three,
        int n_threads,
        int bufsize,
        )
#    void get_optimal_bipart(int full_set, int *left, int *right, int *weights, 
#            int *two2three)
cdef extern from "lookup_table.h":
    void fill_two2three(int *two2three, int n)

def zero_array(n, type_code='i'):
    """Creates an n-long zeroed out Python array, default type int."""
    cdef array.array array_template = array.array(type_code, [])
    cdef array.array newarray
    newarray = array.clone(array_template, n, zero=True)

    return newarray


def py_combinations_2(n):
    """Return n choose 2."""
    return combinations_2(n)

def create_two2three(n):
    """Create an array whose ith element is the number i, with 3^n instead
    of 2^n in the binary expansion of."""

    ar = zero_array(2**n, 'i')

    cdef int[::1] ar_memview = ar

    fill_two2three(&ar_memview[0], n)

    return ar

def py_compressed_weight_rep(
        subsets, start_i, end_i, biparts_a, biparts_b, bipart_weights,
        n_species, n_threads=8, bufsize=3*10**7,
        ):
    """Computes the compressed representation of the bipartition weights."""
    # Copy the lists to arrays, to make them usable in C code
    ar_subsets = array.array('i', subsets)
    ar_start_i = array.array('i', start_i)
    ar_end_i = array.array('i', end_i)
    ar_biparts_a = array.array('i', biparts_a)
    ar_biparts_b = array.array('i', biparts_b)
    ar_bipart_weights = array.array('i', bipart_weights)
    n_subsets = len(subsets)

    two2three = create_two2three(n_species)
    cdef int[::1] two2three_memview = two2three

    weights = zero_array(2*3**(n_species-1), 'i')
    cdef int[::1] weights_memview = weights

    cdef int[::1] subsets_memview = ar_subsets
    cdef int[::1] start_memview = ar_start_i
    cdef int[::1] end_memview = ar_end_i
    cdef int[::1] biparts_a_memview = ar_biparts_a
    cdef int[::1] biparts_b_memview = ar_biparts_b
    cdef int[::1] bipart_weights_memview = ar_bipart_weights

    threads_str = 'thread'
    if n_threads > 1:
        threads_str += 's'

    print("Starting parallel comptuation with a max of {} {}.".
            format(n_threads, threads_str)
    )
    sig_on()
    fill_compressed_weight_representation(
            &subsets_memview[0],
            &start_memview[0],
            &end_memview[0],
            &biparts_a_memview[0],
            &biparts_b_memview[0],
            &bipart_weights_memview[0],
            n_subsets,
            n_species,
            &weights_memview[0],
            &two2three_memview[0],
            n_threads,
            bufsize,
            )
    sig_off()

    return weights

def py_n_common_triplets(int a, int b, int c, int d):
    return n_common_triplets(a, b, c, d)
