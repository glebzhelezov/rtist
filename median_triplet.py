#!/usr/bin/env python
import argparse
from median_tree_reconstruction import median_triplet_trees


def main():
    parser = argparse.ArgumentParser(
        description="reads in a file of Newick strings, and outputs with all the median triplet trees."
    )
    parser.add_argument("i", action="store", type=str, help="input file")
    parser.add_argument("o", action="store", type=str, help="output file")
    parser.add_argument(
        "--nthreads",
        action="store",
        type=int,
        default=1,
        help="maximum number of concurrent threads (default 1)",
    )

    result = parser.parse_args()

    in_file = result.i
    out_file = result.o
    n_threads = result.nthreads

    # This should be refactored, but will work for now.
    with open(in_file, 'r') as f:
        nwks = [line.strip() for line in f]

    print("Finding median tree. This might take a while!")
    median_nwks = median_triplet_trees(nwks, n_threads=n_threads)
    print("Done!")

    with open(out_file, 'w') as f:
        f.writelines([s + '\n' for s in median_nwks])
    print("Wrote result to output.")


if __name__ == "__main__":
    main()
