/* This file was automatically generated.  Do not edit! */
#undef INTERFACE
void calculate_two2three(int **two2three,int n);
void get_compressed_weight_representation(int *left_sets,int *right_sets,int *bipart_weights,int n_biparts,int n_species,int **weights,int n_threads);
int compressed_rep(int a,int b,int *two2three);
int ipow(int a,int b);
void fill_compressed_weight_representation(int *subsets,int *start_i,int *end_i,int *left_sets,int *right_sets,int *bipart_weights,int n_subsets,int n_species,int *weights,int *two2three,int n_threads, int bufsize);
int n_common_triplets_avx(int a,int b,int c,int d);
int n_common_triplets(int a,int b,int c,int d);
int first_n_combo(int universe,int n);
int snoob(int sub,int universe);
int combinations_2(int n);
