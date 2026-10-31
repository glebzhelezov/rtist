#ifndef MTRIP_LOOKUP_TABLE_H
#define MTRIP_LOOKUP_TABLE_H

/* a^b for small non-negative b. */
int ipow(int a, int b);

/* Fill two2three (2^n entries) so that two2three[x] has the same digits as x,
 * read in base 3 instead of base 2. */
void fill_two2three(int *two2three, int n);

/* Allocate (with malloc) and fill a two2three table. *two2three is NULL if
 * the allocation fails. */
void calculate_two2three(int **two2three, int n);

/* Base-3 representation of the bipartition (a,b): the smaller of
 * a_3 + 2*b_3 and 2*a_3 + b_3, so (a,b) and (b,a) map to the same index.
 * two2three must have been filled. */
int compressed_rep(int a, int b, int *two2three);

#endif /* MTRIP_LOOKUP_TABLE_H */
