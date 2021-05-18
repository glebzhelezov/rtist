#!/usr/bin/env python
import argparse
import sys
import pickle
import median_triplet_version
from time import time
from datetime import timedelta
from os import cpu_count
from os.path import basename
from median_tree_reconstruction import median_triplet_trees


# Some fun colors. Should be refactored. Or removed. :-)
bold = "\033[1m"
underline = "\033[4m"
italics = "\033[3m"
end = "\033[0m"

# Trick by Steven Berthard
# https://groups.google.com/g/argparse-users/c/LazV_tEQvQw
# https://stackoverflow.com/questions/4042452/display-help-message-with-python-argparse-when-script-is-called-without-any-argu
class FriendlyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("error: {}\n".format(message))
        self.print_help()
        sys.exit(2)

def get_parser():
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
        "-v", "--version", action="version", version=median_triplet_version.__version__,
    )
    parser.add_argument(
        "-t",
        "--threads",
        action="store",
        type=int,
        default=-1,
        help="maximum number of concurrent threads (defaults to number of CPUs, or 1 if undetermined). Must be a positive integer or -1 for the default guess",
    )
    parser.add_argument(
        "--novalidate",
        action="store_true",
        help="don't perform line-by-line sanity check for each input Newick string (for a small speedup)",
        default=False,
    )
    parser.add_argument(
        "-n",
        "--nosave",
        action="store_true",
        help="don't save the output to a file (must be used with --print)",
        default=False,
    )
    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="print the output to the screen",
        default=False,
    )
    parser.add_argument(
        "-b",
        "--binary",
        action="store",
        type=str,
        help="save the weights array to a binary file. This file can be used to find additional trees. Traditionally this file has the extension .p",
    )

    return parser

def main():
    tic = time()

    parser = get_parser()
    result = parser.parse_args()

    in_file = result.i
    out_file = result.o
    n_threads = result.threads
    novalidate = result.novalidate
    nosave = result.nosave
    printflag = result.print
    picklename = result.binary

    if nosave and not printflag:
        print(
            "The flag --nosave cannot be used without --print, otherwise the output goes nowhere. Aborting."
        )
        return 1

    if not (n_threads >= 1 or n_threads == -1):
        print("The number of threads must be a positive integer or -1.")
        return 1

    if out_file is None:
        out_file = "out_" + basename(in_file)

    # Set default maximum number of threads.
    if n_threads == -1:
        n_threads = cpu_count()
    if n_threads is None:
        n_threads = 1

    print(underline + "Input parameters:" + end)
    print("Newick file: {}".format(in_file))
    if nosave:
        print("Output file: outputting to stdout instead.")
    else:
        print("Output file: {}".format(out_file))

    print("Max threads: {}".format(n_threads))
    if novalidate:
        print("Not validating Newick strings!")

    print("")

    # This should be refactored, but will work for now.
    try:
        print(underline + "Parsing input text file." + end)
        with open(in_file, "r") as f:
            print("* Stripping Newick strings.")
            nwks = [line.strip() for line in f]
    except IOError:
        print("Can't open input file {} for reading. Aborting.".format(in_file))
        return 1

    if not novalidate:
        print("* Checking for matching parentheses and semicolon in each GT.")
        for i, string in enumerate(nwks):
            # Ignore comments
            if string[0] == "#":
                continue
            # Need to put in a stricter validator here
            if string[-1] != ";":
                print("Line {} doesn't end of a semicolon! Aborting!".format(i + 1))
                return 1
            if string.count("(") != string.count(")"):
                print(
                    "Line {} doesn't have an equal number of left and right brackets! Aborting!".format(
                        i + 1
                    )
                )
                return 1

    # Get rid of comments
    nwks[:] = [s for s in nwks if s[0] != '#']

    print("")
    print(underline + "Finding median tree. This might take a while!" + end)
    (
        median_nwks,
        reverse_dictionary,
        triplet_weights,
        stack,
        best_biparts,
    ) = median_triplet_trees(nwks, n_threads=n_threads, return_extra=True)

    print("")
    print("{}{}Done!{}{}".format(bold, underline, end, end))
    # Save output
    if not nosave:
        try:
            with open(out_file, "w") as f:
                f.writelines([s + "\n" for s in median_nwks])
            print(
                "* {}Wrote all median triplet trees to {}{}{}.".format(
                    bold, italics, out_file, end, end
                )
            )
        except IOError:
            print("Can't write to {}. Outputting to stdout instead.".format(outfile))
            # If can't write to file, output to screen as a last resort
            printflag = True

    toc = time()
    dt = timedelta(seconds=toc - tic)

    print("🤖💬 Beep boop, finished in {:.2f} seconds.".format(dt.total_seconds()))

    if printflag:
        print("")
        for s in median_nwks:
            print(s)
        # print("")

    # Pickle stuff
    if picklename is not None:
        try:
            with open(picklename, "wb") as f:
                labels = [
                    "abigsecret",
                    "version",
                    "nwks",
                    "median_nwks",
                    "reverse_dictionary",
                    "triplet_weights",
                    "stack",
                    "best_biparts",
                ]
                to_pickle = [
                    "ogurets",
                    median_triplet_version.__version__,
                    nwks,
                    median_nwks,
                    reverse_dictionary,
                    triplet_weights,
                    stack,
                    best_biparts,
                ]

                pickle.dump({l: t for (l, t) in zip(labels, to_pickle)}, f, protocol=4)

                # for item in to_pickle:
                #    pickle.dump(item, f, protocol=4)
            print(
                "* {}Pickled weights to {}{}{}. 🥒🏋️".format(
                    bold, italics, picklename, end, end
                )
            )
        except IOError:
            print(
                "Can't write to {}. Aborting serializing the processed data.".format(
                    picklename
                )
            )

    return 0


if __name__ == "__main__":
    sys.exit(main())
