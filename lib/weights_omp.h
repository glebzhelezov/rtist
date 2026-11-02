#ifndef MTRIP_WEIGHTS_OMP_H
#define MTRIP_WEIGHTS_OMP_H

/* n choose 2. */
int combinations_2(int n);

/* Next largest number with the same number of set bits as sub, with bits only
 * where universe has bits (Gosper's hack). */
int snoob(int sub, int universe);

/* First (smallest) number with n set bits, with bits only where universe has
 * bits. Returns -1 if universe has fewer than n set bits. */
int first_n_combo(int universe, int n);

/* Number of triplets common to the bipartitions (a,b) and (c,d). */
int n_common_triplets(int a, int b, int c, int d);

/* Expand the observed bipartition weights into the weight of every possible
 * bipartition, indexed by its base-3 representation (see compressed_rep).
 *
 * The observed bipartitions are grouped by the subset they partition: for
 * subset subsets[k], its bipartitions are (left_sets[i], right_sets[i]) with
 * weights bipart_weights[i], for start_i[k] <= i < end_i[k].
 *
 * weights must hold 2 * 3^(n_species - 1) entries, all zero on entry.
 * two2three must have been filled by fill_two2three(two2three, n_species).
 * n_threads is ignored when built without OpenMP.
 *
 * Progress goes to stderr, depending on verbosity: 0 prints nothing, 1 the
 * thread count and a final summary line, 2 also a live progress counter. */
void fill_compressed_weight_representation(int *subsets, int *start_i,
                                           int *end_i, int *left_sets,
                                           int *right_sets, int *bipart_weights,
                                           int n_subsets, int n_species,
                                           int *weights, int *two2three,
                                           int n_threads, int verbosity);

#endif /* MTRIP_WEIGHTS_OMP_H */
