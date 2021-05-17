#!/usr/bin/env python
import argparse
import sys
import median_triplet_version
from time import time
from datetime import timedelta
from os import cpu_count
from os.path import basename
from median_tree_reconstruction import median_triplet_trees

# Trick by Steven Berthard
# https://groups.google.com/g/argparse-users/c/LazV_tEQvQw
# https://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
class FriendlyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: %s\n" % message)
        self.print_help()
        sys.exit(2)


def main():
    tic = time()
    parser = FriendlyParser(
        description="Reads in a file of Newick strings, and outputs a file with all the median triplet trees."
    )
    parser.add_argument(
        "i",
        action="store",
        type=str,
        help="input file with one Newick string per line",
    )
    parser.add_argument(
        "o",
        nargs="?",
        action="store",
        type=str,
        help="output file (warning: any existing file will be overwritten!). Defaults to out_<input file>",
        default=None,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=median_triplet_version.__version__,
    )
    parser.add_argument(
        "-t",
        "--threads",
        action="store",
        type=int,
        default=-1,
        help="maximum number of concurrent threads (defaults to number of CPUs, or 1 if undetermined)",
    )
    parser.add_argument(
        "-n",
        "--novalidate",
        action="store_true",
        help="don't perform line-by-line sanity check for each input Newick string (for a small speedup)",
        default=False,
    )

    result = parser.parse_args()

    in_file = result.i
    out_file = result.o
    n_threads = result.threads
    novalidate = result.novalidate

    if out_file is None:
        out_file = "out_" + basename(in_file)

    # Set default maximum number of threads.
    if n_threads == -1:
        n_threads = cpu_count()
    if n_threads is None:
        n_threads = 1

    print("Newick file: {}".format(in_file))
    print("Output file: {}".format(out_file))
    print("Max threads: {}".format(n_threads))
    if novalidate:
        print("Not validating Newick strings!")
    print("")

    # This should be refactored, but will work for now.
    try:
        with open(in_file, "r") as f:
            print("* Stripping Newick strings.")
            nwks = [line.strip() for line in f]
    except IOError:
        print("Can't open input file {} for reading. Aborting.".format(in_file))
        return 1

    if not novalidate:
        print("* Checking for matching parentheses and semicolon in each GT.")
        for i, string in enumerate(nwks):
            # Need to put in a strictor validator here
            if string[-1] != ";":
                print(
                    "Line {} doesn't end of a semicolon! Aborting!".format(
                        i + 1
                    )
                )
                return 1
            if string.count("(") != string.count(")"):
                print(
                    "Line {} doesn't have an equal number of left and right brackets! Aborting!".format(
                        i + 1
                    )
                )
                return 1

    print("Finding median tree. This might take a while!")
    median_nwks = median_triplet_trees(nwks, n_threads=n_threads)

    try:
        with open(out_file, "w") as f:
            f.writelines([s + "\n" for s in median_nwks])
        print("* Wrote all median triplet trees to {}.".format(out_file))
    except IOError:
        print(
            "Can't open output file {} for writing. Outputting to stdout instead.".format(
                outfile
            )
        )
        print("")
        for s in median_nwks:
            print(s)
        print("")

    toc=time()

    print("* Finished in {} hours:minutes:seconds.".format(timedelta(seconds=toc-tic)))

    return 0


if __name__ == "__main__":
    sys.exit(main())
