#include "weights_omp.h"
#include "lookup_table.h"
#include <math.h>
#include <stdio.h>
#include <stdlib.h>

// Only include OpenMP if not explicitly disabled
#ifndef NO_OMP
#include <omp.h>
#endif

/* Calculate n choose 2. */
inline int combinations_2(int n) { return (n * (n - 1)) / 2; }

/* Calculate the next largest number with the same number of bits, with
 * bits only where universe has bits. Algorithm by Bill Gosper. */
int snoob(int sub, int universe) {
    int tmp = sub - 1;
    int rip = universe & (tmp + (sub & (-sub)) - universe);

    sub = (tmp & sub) ^ rip;
    sub &= sub - 1;

    while (sub > 0) {
        tmp = universe & (-universe);
        rip ^= tmp;
        universe ^= tmp;
        sub &= sub - 1;
    }

    return rip;
}

/* Calculate the first number with n set bits, which only has set bits where
 * universe has set bits. */
int first_n_combo(int universe, int n) {
    if (__builtin_popcount(universe) < n) {
        printf("Popcount of universe is too small!\n");
        return -1;
    }

    int t = universe;

    for (int i = 0; i < n; i++) {
        t ^= t & (-t);
    }

    return universe ^ t;
}

/* The number of common triplets to the sub-bipartitions (a,b) and (c,d). */
int n_common_triplets(int a, int b, int c, int d) {
    int total = 0;

    int n_ac = __builtin_popcount(a & c);
    int n_ad = __builtin_popcount(a & d);
    int n_bc = __builtin_popcount(b & c);
    int n_bd = __builtin_popcount(b & d);

    total = combinations_2(n_ac) * n_bd + combinations_2(n_ad) * n_bc +
            combinations_2(n_bc) * n_ad + combinations_2(n_bd) * n_ac;

    return total;
}

int n_common_triplets_avx(int a, int b, int c, int d) {
    int total = 0;

    int n_ac = __builtin_popcount(a & c);
    int n_ad = __builtin_popcount(a & d);
    int n_bc = __builtin_popcount(b & c);
    int n_bd = __builtin_popcount(b & d);

    total = combinations_2(n_ac) * n_bd + combinations_2(n_ad) * n_bc +
            combinations_2(n_bc) * n_ad + combinations_2(n_bd) * n_ac;

    return total;
}

void fill_compressed_weight_representation(
    int *subsets, int *start_i, int *end_i, int *left_sets, int *right_sets,
    int *bipart_weights, int n_subsets, int n_species,
    int *weights, /* Must be allocated with 0 in each entry. */
    int *two2three, int n_threads) {
    /* Iterate over all the (sub)bi-partitions. */
    int loop_progress = 0;
    
    #ifndef NO_OMP
    #pragma omp parallel num_threads(n_threads)
    {
        /* Get actual number of threads, and this thread's ID */
        int n_threads_assigned = omp_get_num_threads();
        int thread_id_private = omp_get_thread_num();
        /* Print out number of threads */
        if (thread_id_private == 0) {
            printf("Using %d threads.\n", n_threads_assigned);
        }
    #else
    {
        /* Single-threaded version */
        printf("Using 1 thread (OpenMP not available).\n");
        int n_threads_assigned = 1;
        int thread_id_private = 0;
    #endif
        
        /* Calculate the progress this thread is making, to eventually add
         * to the progress bar. */
        int counter_private = 0;
        /* Update total counter every output_step number of steps */
        int output_step = round(n_subsets / (100 * n_threads_assigned));
        output_step = (output_step > 1) ? output_step : 1;
        /* This is the binary number with 1s everywhere, which represents the
         * set of all species in the data. */
        int universe = (1 << n_species) - 1;
        /* Iterate over all possible values of a+b, where (a,b) is a bipart. */
        
    #ifndef NO_OMP
    #pragma omp for schedule(static)
    #endif
        for (int subset_i = 0; subset_i < n_subsets; subset_i++) {
            int bitmask = subsets[subset_i];
            int kernel = universe - bitmask;

            /* This iterates over all numbers with bits set only where
             * bitmask has set bits, excluding bitmask. */
            int a_prime = bitmask & (bitmask - 1);

            /* We should iterate over possible a+b sums */
            for (int a_prime = bitmask & (bitmask - 1); a_prime > 0;
                 a_prime = bitmask & (a_prime - 1)) {
                int bitmask_inner = bitmask - a_prime;

                /* This iterates over all numbers with bits set only where
                 * bitmask_inner set bits, and strictly less than
                 * a_prime. Includes self. */
                int b_prime = bitmask_inner;
                for (int b_prime = bitmask_inner; b_prime > 0;
                     b_prime = bitmask_inner & (b_prime - 1)) {
                    if (b_prime < a_prime) {
                        /* Find the contribution of each bipart which has this
                         * exact kernel. */
                        int weight_increment = 0;
                        for (int i = start_i[subset_i]; i < end_i[subset_i];
                             i++) {
                            weight_increment +=
                                bipart_weights[i] *
                                n_common_triplets(a_prime, b_prime,
                                                  left_sets[i], right_sets[i]);
                        }

                        /* (a'+k1, b'+k2) has the same number of GT triplets
                         * as (a', b'), so let's update them all in one sweep */
                        for (int k1 = kernel; k1 >= 0; k1 = kernel & (k1 - 1)) {
                            for (int k2 = kernel - k1; k2 >= 0;
                                 k2 = (kernel - k1) & (k2 - 1)) {
                                int x = a_prime + k1;
                                int y = b_prime + k2;

                                /* Base-3 representation of bipart */
                                int rep = compressed_rep(x, y, two2three);

                                /* Update the weights array */
                                #ifndef NO_OMP
                                #pragma omp atomic update
                                #endif
                                weights[rep] += weight_increment;

                                /* This is necessary to break out of an endless
                                 * loop! */
                                if (k2 == 0) {
                                    break;
                                }
                            }
                            /* This is necessary to break out of an endless
                             * loop! */
                            if (k1 == 0) {
                                break;
                            }
                        }
                    }
                }
            }
            counter_private++;

            if (counter_private % output_step == 0) {
                /* Update the overall counter one thread at a time */
                #ifndef NO_OMP
                #pragma omp atomic update
                #endif
                loop_progress = loop_progress + counter_private;
                counter_private = 0;
                /* Only update the progress bar by the master thread */
                if (thread_id_private == 0) {
                    /* Progress bar temporarily disabled */
                    fprintf(stderr, "\r%d/%d complete (%.2f%%)", loop_progress,
                            n_subsets, (100.0 * loop_progress) / n_subsets);
                    fflush(stderr);
                }
            }
        }
    }
    fprintf(stderr, "\r");
    fflush(stderr);
    printf("%d/%d complete (%.2f%%)\n", n_subsets, n_subsets, 100.0);
    fflush(stdout);
}