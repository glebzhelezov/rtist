#include <stdio.h>
#include <stdlib.h>
#include <omp.h>
#include <math.h>
#include "weights_omp.h"
#include "lookup_table.h"
#include "progressbar.h"
#include "statusbar.h"

/*
   int main() {
   int left_sets[] = {5,2,15,4,3,1,2,4,2,7,5};
   int right_sets[] = {8,13,16,9,12,12,9,11,5,8,10};
   int bipart_weights[] = {10,37,50,12,5,15,5,5,1,1,2};
   int n_biparts = 11;
   int n_species = 16;

   int *weights;
// Do the calculations B-)
int n_threads = 1;
get_compressed_weight_representation(left_sets, right_sets, bipart_weights,
n_biparts, n_species, &weights, n_threads);

int left, right;
int *two2three;
calculate_two2three(&two2three, n_species);
//get_optimal_bipart(ipow(2,n_species)-1, &left, &right, weights, two2three);

// Should probably create a separate function like,
// fill_compressed_rep_matrix( .... ) so it can be called directly
// from Python with NumPy arrays. 

printf("[");
for (int i=0; i<2*3*3*3*3; i++) {
printf("%d, ", weights[i]);
}
printf("]");
free(weights);
free(two2three);

return 0;
}
*/

/* Calculate n choose 2. */
inline int combinations_2(int n) {
    return (n*(n-1))/2;
}


/* Calculate the next largest number with the same number of bits, with
 * bits only where universe has bits. Algorithm by Bill Gosper. */
int snoob(int sub, int universe) {
    int tmp = sub - 1;
    int rip = universe&(tmp + (sub&(- sub)) - universe);

    sub = (tmp&sub)^rip;
    sub &= sub-1;

    while (sub>0) {
        tmp = universe&(-universe);
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

    for (int i=0; i<n; i++) {
        t ^= t&(-t);
    }

    return universe^t;
}



/* The number of common triplets to the sub-bipartitions (a,b) and (c,d). */
int n_common_triplets(int a, int b, int c, int d) {
    int total = 0;

    int n_ac = __builtin_popcount(a&c);
    int n_ad = __builtin_popcount(a&d);
    int n_bc = __builtin_popcount(b&c);
    int n_bd = __builtin_popcount(b&d);

    total = combinations_2(n_ac)*n_bd
        + combinations_2(n_ad)*n_bc
        + combinations_2(n_bc)*n_ad
        + combinations_2(n_bd)*n_ac;

    return total;
}

int n_common_triplets_avx(int a, int b, int c, int d) {
    int total = 0;

    int n_ac = __builtin_popcount(a&c);
    int n_ad = __builtin_popcount(a&d);
    int n_bc = __builtin_popcount(b&c);
    int n_bd = __builtin_popcount(b&d);

    total = combinations_2(n_ac)*n_bd
        + combinations_2(n_ad)*n_bc
        + combinations_2(n_bc)*n_ad
        + combinations_2(n_bd)*n_ac;

    return total;
}


void fill_compressed_weight_representation(
        int *subsets,
        int *start_i,
        int *end_i,
        int *left_sets,
        int *right_sets,
        int *bipart_weights,
        int n_subsets,
        int n_species,
        int *weights, /* Must be allocated with 0 in each entry. */
        int *two2three,
        int n_threads,
        int bufsize) {
    //printf("meow\n");
    /* Iterate over all the (sub)bi-partitions. */
    /*int bufsize = atoi(getenv("TRIPLET_BUFSIZE"));*/
    int loop_progress = 0;
    /* We'll make the buffer sizes slightly different to avoid
     * unnecessary locks. Set the seed to 0 for reproducibility. */
    srand(0);
    progressbar *progbar = progressbar_new("Progress", n_subsets);
#pragma omp parallel num_threads(n_threads)
    {
        int private_bufsize = (int) ((0.7 + 0.3*(rand()%200)/100)*bufsize);
        /* int private_bufsize = int(0.7*bufsize) + (0.3*bufsize(rand() % 200)/100.0);*/
        /* int *weights_private = calloc(2*ipow(3,n_species-1), sizeof(int)); */
        int *weights_buffer = calloc(private_bufsize, sizeof(int));
        int *positions_buffer = calloc(private_bufsize, sizeof(int));
        int buffer_position=0;
        int counter_private = 0;
        int n_threads_assigned = omp_get_num_threads();
        int output_step = round(n_subsets/(100*n_threads_assigned));
        output_step = (output_step > 1) ? output_step : 1;
        int thread_id_private = omp_get_thread_num();
        int universe = (1<<n_species) - 1;
        /* Iterate over all possible values of a+b, where (a,b) is a bipart. */
#pragma omp for schedule(dynamic)
        for (int subset_i=0; subset_i<n_subsets; subset_i++) {
            int bitmask = subsets[subset_i];
            /* 1<<n_species == 2^n_species; */
            /*int a = left_sets[i];
              int b = right_sets[i];*/
            int kernel = universe - bitmask;

            /* This iterates over all numbers with bits set only where
             * bitmask has set bits, excluding bitmask. */
            int a_prime = bitmask & (bitmask - 1);
            /*int bipart_weight = bipart_weights[i];*/

            /* We should iterate over possible a+b sums */
            for (int a_prime=bitmask&(bitmask-1); a_prime>0;
                    a_prime=bitmask&(a_prime-1)) {
                int bitmask_inner = bitmask - a_prime;

                /* This iterates over all numbers with bits set only where
                 * bitmask_inner set bits, and strictly less than
                 * a_prime. Includes self. */
                int b_prime = bitmask_inner;
                for (int b_prime=bitmask_inner; b_prime>0; 
                        b_prime=bitmask_inner&(b_prime-1)) {
                    if (b_prime < a_prime) {
                        /* Find the contribution of each bipart which has this
                         * exact kernel. */
                        int weight_increment=0;
                        for (int i = start_i[subset_i]; i < end_i[subset_i]; i++) {
                            weight_increment += bipart_weights[i]*n_common_triplets(
                                    a_prime, b_prime, left_sets[i], right_sets[i]);
                        }

                        /* (a'+k1, b'+k2) has the same number of GT triplets
                         * as (a', b'), so let's update them all in one sweep */
                        for (int k1=kernel; k1>=0; k1=kernel&(k1-1)) {
                            for (int k2=kernel-k1; k2>=0; 
                                    k2=(kernel-k1)&(k2-1)) {
                                int x = a_prime + k1;
                                int y = b_prime + k2;

                                /* Put in code to calculate common # triplets. */
                                /* Update precomputed weights. */
                                int rep = compressed_rep(x, y, two2three);

                                //weights_private[rep] += n_triplets * bipart_weight;
                                /*weights_private[rep] += weight_increment;*/
                                /* We'll add this to the global weights array later */
                                weights_buffer[buffer_position] += weight_increment;
                                positions_buffer[buffer_position] = rep;
                                buffer_position++;

                                /* Check if it's time to update the weights
                                 * array */
                                if (buffer_position == private_bufsize) {
                                    /* Only one thread accesses array to update */
# pragma omp critical
                                    for (int i=0; i<private_bufsize; i++) {
                                        weights[positions_buffer[i]] += 
                                            weights_buffer[i];
                                    }
                                    /* reset everything */
                                    buffer_position = 0;
                                    memset(weights_buffer, 0, private_bufsize*sizeof(int));
                                    /* For large-ish arrays it is faster to calloc */
                                    /*free(weights_buffer);
                                    weights_buffer = calloc(private_bufsize, sizeof(int));*/

                                }

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
# pragma omp atomic update
                loop_progress = loop_progress + counter_private;
                counter_private = 0;

                if (thread_id_private == 0) {
                    /*printf("Loop progress: %d\n", loop_progress);*/
                    progressbar_update(progbar, loop_progress);
                    //fflush(stdout);
                }
            }
        }
            /* Need to add in updates from partially-full buffers */
# pragma omp critical
        {
            for (int i=0; i<buffer_position; i++) {
                weights[positions_buffer[i]] += weights_buffer[i];
            }
            /*for (int i=0; i<2*ipow(3,n_species-1); i++) {
                weights[i] += weights_private[i];
            }*/
        }
        /*free(weights_private);*/
        free(weights_buffer);
        free(positions_buffer);
    }
    progressbar_update(progbar, n_subsets);
    progressbar_finish(progbar);

}


// void get_compressed_weight_representation(
//         int *left_sets,
//         int *right_sets,
//         int *bipart_weights,
//         int n_biparts,
//         int n_species,
//         int **weights,
//         int n_threads) {
// 
//     /* Calculate the two2three arrya necessary for quick bipart encoding. */
//     int *two2three;
//     calculate_two2three(&two2three, n_species);
// 
//     /*int weights_size = (int)(pow(3, n_species-1) + 0.5);*/
//     int weights_size = 2*ipow(3, n_species-1);
//     /*int *weights;*/
//     *weights = calloc(weights_size, sizeof(int));
//     if (weights == NULL) {
//         printf("Failed to create weights array.\n");
//         return;
//     }
// 
//     fill_compressed_weight_representation(left_sets, right_sets, bipart_weights,
//             n_biparts, n_species, *weights, two2three, n_threads);
// 
//     free(two2three);
// 
//     return;
// }


