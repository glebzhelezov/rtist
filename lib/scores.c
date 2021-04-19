#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include "scores.h"
#include "lookup_table.h"

/* The functions in this generate generate the weights of all the
 * bipartitions present in the GTs. */

// /* This is just for testing. */
// int main_test() {
//     int left_sets[] = {5,2,15,4,3,1,2,4,2,7,5};
//     int right_sets[] = {8,13,16,9,12,12,9,11,5,8,10};
//     int weights[] = {10,37,50,12,5,15,5,5,1,1,2};
//     int n_biparts = 11;
//     int n_species = 5;
// 
//     int *scores;
//     /* Do the calculations B-) */
//     get_compressed_score_representation(left_sets, right_sets, weights,
//             n_biparts, n_species, &scores);
// 
//     int left, right;
//     int *two2three;
//     calculate_two2three(&two2three, n_species);
//     /*get_optimal_bipart(ipow(2,n_species)-1, &left, &right, scores, two2three);*/
// 
//     /*printf("Best decomposition: %d %d\n", left, right);*/
//     /* Should probably create a separate function like,
//      * fill_compressed_rep_matrix( .... ) so it can be called directly
//      * from Python with NumPy arrays. */
// 
//     printf("[");
//     for (int i=0; i<2*3*3*3*3; i++) {
//         printf("%d, ", scores[i]);
//     }
//     printf("]");
//     free(scores);
//     free(two2three);
// 
//     return 0;
// }
// 
// /* Calculate n choose 2. */
// int combinations_2(int n) {
//     if (n >= 2) {
//         return (n*(n-1))/2;
//     } else {
//         return 0;
//     }
// }



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


void fill_compressed_score_representation(
        int *left_sets,
        int *right_sets,
        int *weights,
        int n_biparts,
        int n_species,
        int *scores, /* Must be allocated with 0 in each entry. */
        int *two2three) {
    /* Iterate over all the (sub)bi-partitions. */
    for (int i=0; i<n_biparts; i++) {
        /* 1<<n_species == 2^n_species; */
        int a = left_sets[i];
        int b = right_sets[i];
        int kernel = (1<<n_species) - 1 - a - b;
        
        int bitmask = left_sets[i] + right_sets[i];

        /* This iterates over all numbers with bits set only where
         * bitmask has set bits, excluding bitmask. */
        int a_prime = bitmask & (bitmask - 1);
        while (a_prime > 0) {
            int bitmask_inner = bitmask - a_prime;

            /* This iterates over all numbers with bits set only where
             * bitmask_inner set bits, and strictly less than
             * a_prime. Includes self. */
            int b_prime = bitmask_inner;
            while (b_prime > 0) {
                if (b_prime < a_prime) {
                    int k1 = kernel;
                    /* This is to avoid getting stuck in an infinte loop. */
                    int prev_k1 = -1;
                    while (k1 >= 0) {
                        int k2 = kernel - k1;
                        /* This is to avoid getting stuck in an infinte loop. */
                        int prev_k2 = -1;
                        while (k2 >= 0) {
                            int x = a_prime + k1;
                            int y = b_prime + k2;

                            /* Put in code to calculate common # triplets. */
                            int n_triplets = n_common_triplets(
                                    x, y, a, b);
                            /* Update precomputed scores. */
                            int rep = compressed_rep(x, y, two2three);
                            scores[rep] += n_triplets * weights[i];

                            /* This is necessary to break out of an endless
                             * loop! */
                            if (k2 == 0) {
                                break;
                            }
                            /* Update value of k2 */
                            k2 = (kernel-k1) & (k2-1);
                        }
                        /* This is necessary to break out of an endless
                         * loop! */
                        if (k1 == 0) {
                            break;
                        }
                        /* Update value of k1 */
                        k1 = kernel & (k1-1);
                    }
                }
                b_prime = bitmask_inner & (b_prime-1);
            }
            a_prime = bitmask & (a_prime-1);
        }
    }

}


void get_compressed_score_representation(
        int *left_sets,
        int *right_sets,
        int *weights,
        int n_biparts,
        int n_species,
        int **scores) {

    /* Calculate the two2three arrya necessary for quick bipart encoding. */
    int *two2three;
    calculate_two2three(&two2three, n_species);

    /*int scores_size = (int)(pow(3, n_species-1) + 0.5);*/
    int scores_size = 2*ipow(3, n_species-1);
    /*int *scores;*/
    *scores = calloc(scores_size, sizeof(int));
    if (scores == NULL) {
        printf("Failed to create scores array.\n");
        return;
    }

    fill_compressed_score_representation(left_sets, right_sets, weights,
            n_biparts, n_species, *scores, two2three);

    free(two2three);

    return;
}


/* void get_optimal_bipart(int set, int *left, int *right, int *scores, 
        int *two2three) {
    if (__builtin_popcount(set)<3) {
        *left=0;
        *right=set;
    }

    int max = -1;
    int left_candidate, right_candidate;

    for (int subset=set&(set-1); subset=set&(subset-1); subset>0) {
        int complement = set-subset;
        if (subset<complement) {
            int bipart_index = compressed_rep(subset, complement, two2three);
            if (scores[bipart_index]>max) {
                max = scores[bipart_index];
                left_candidate = subset;
                right_candidate = complement;
            }
        }
    }

    *left = left_candidate;
    *right = right_candidate;

    return;
}
*/
