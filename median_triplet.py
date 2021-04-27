#!/usr/bin/env python
import argparse
import sys
from os import cpu_count
from os.path import basename
from median_tree_reconstruction import median_triplet_trees

# Trick by Steven Berthard
# https://groups.google.com/g/argparse-users/c/LazV_tEQvQw
# https://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
class FriendlyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)

def main():
    parser = FriendlyParser(
        description="Reads in a file of Newick strings, and outputs a file with all the median triplet trees."
    )
    parser.add_argument("i", action="store", type=str, help="input file with one Newick string per line")
    parser.add_argument(
        "-t",
        "--threads",
        action="store",
        type=int,
        default=-1,
        help="maximum number of concurrent threads (defaults to number of CPUs, or 1 if undetermined)",
    )
    parser.add_argument("-o", "--outfile", action="store", type=str, help="output file (warning: any existing file will be overwritten!). Defaults to out_<input file>", default=None)

    result = parser.parse_args()

    in_file = result.i
    out_file = result.outfile
    n_threads = result.threads

    if out_file is None:
        out_file = "out_" + basename(in_file)

    # Set default maximum number of threads.
    if n_threads == -1:
        n_threads = cpu_count()
    if n_threads is None:
        n_threads = 1

    # This should be refactored, but will work for now.
    with open(in_file, 'r') as f:
        nwks = [line.strip() for line in f]

    print("Reading Newick strings from {}.\nOutputting result to {}.\nMax number of threads set to {}.\n".format(in_file, out_file, n_threads))
    print("Finding median tree. This might take a while!")
    median_nwks = median_triplet_trees(nwks, n_threads=n_threads)
    print("Done!")

    with open(out_file, 'w') as f:
        f.writelines([s + '\n' for s in median_nwks])
    print("Wrote result to output file.")


if __name__ == "__main__":
    main()
