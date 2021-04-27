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

def py_compressed_weight_rep(bipart_weights, n_species, n_threads=8):
    """Computes the compressed representation of the bipartition weights."""
    n_biparts = len(bipart_weights)
    ls = zero_array(n_biparts, 'i')
    rs = zero_array(n_biparts, 'i')
    ws = zero_array(n_biparts, 'i')

    for (i, ((l,r),w)) in enumerate(bipart_weights.items()):
        ls[i]=l
        rs[i]=r
        ws[i]=w

    two2three = create_two2three(n_species)

    weights = zero_array(2*3**(n_species-1), 'i')
    
    arrays_to_c = [ls, rs, ws, weights]

    cdef int[::1] weights_memview = weights
    cdef int[::1] two2three_memview = two2three
    cdef int[::1] ls_memview = ls
    cdef int[::1] rs_memview = rs
    cdef int[::1] ws_memview = ws

    sig_on()
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
    sig_off()

    return weights
