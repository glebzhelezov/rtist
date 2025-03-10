#include "lookup_table.h"
#include "weights_omp.h"
#include <stdio.h>
#include <stdlib.h>

/* The functions in this file basically allow us to work with a base-3
 * representation of a tripartition. */

/* It's probably not necessary to optimize this, since we call this function
 * just a few times. */
int ipow(int a, int b) {
    int product = 1;

    for (int i = 0; i < b; i++) {
        product *= a;
    }

    return product;
}

void fill_two2three(int *two2three, int n) {
    /* Create a lookup table for powers of three. */
    int *pows = malloc(n * sizeof(int));
    if (pows == NULL) {
        printf("Failed to create pows array.\n");
        return;
    }

    for (int i = 0; i < n; i++) {
        pows[i] = ipow(3, i);
    }

    /* The largest number we have to deal with is:
     * 111..(n ones)...1 = 2^n - 1 */
    int array_size = ipow(2, n);

    for (int i = 0; i < array_size; i++) {
        int tot = 0;
        int k = i;
        /* Sum over set bit positions. */
        while (k > 0) {
            /* Count the number of trailing zeroes. */
            tot += pows[__builtin_ctz(k)];
            /* Unset the least set bit. */
            k = k & (k - 1);
        }
        two2three[i] = tot;
    }

    /* Free powers lookup table. */
    free(pows);

    return;
}

/* Finds the matrix two2three such that two2three[(b_n ... n_0)_2] =
 * b_n 3^n + ... + b_0, i.e. keep the coefficients but switch the base
 * from base 2 to base 3. */
void calculate_two2three(int **two2three, int n) {
    /* The largest number we have to deal with is:
     * 111..(n ones)...1 = 2^n - 1 */
    int array_size = ipow(2, n);
    *two2three = malloc(array_size * sizeof(int));
    if (two2three == NULL) {
        printf("Failed to allocate two2three array.\n");
        return;
    }

    fill_two2three(*two2three, n);

    return;
}

/* Returns the compressed representation of the partition (a,b);
 * Note the array two2three must have been filled up. */
int compressed_rep(int a, int b, int *two2three) {
    int a_3 = two2three[a];
    int b_3 = two2three[b];
    int rep1 = a_3 + 2 * b_3;
    int rep2 = 2 * a_3 + b_3;

    /* This calculates the compressed representation. */
    int compressed = (rep1 < rep2) ? rep1 : rep2;

    return compressed;
}

/*
int main() {
    int n = 16;
    int *two2three;
    calculate_two2three(&two2three, n);
    int a = 2 + 4;
    int b = 128 + 8 + 16 + 32;
    int a_3 = two2three[a];
    int b_3 = two2three[b];
    int rep1 = a_3 + 2*b_3;
    int rep2 = 2*a_3 + b_3;
    int comp = compressed_rep(a,b,two2three);
    printf("The compressed rep is %d\n", comp);

    free(two2three);

    return 0;
}*/
