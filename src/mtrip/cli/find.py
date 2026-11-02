import logging
import sys
from os import cpu_count
from os.path import basename
from time import time

import mtrip
from mtrip.cli._common import (
    BOLD,
    ITALICS,
    UNDERLINE,
    FriendlyParser,
    add_common_arguments,
    save_weights,
    setup_logging,
    style,
)
from mtrip.median_tree_reconstruction import median_triplet_trees

log = logging.getLogger("mtrip.cli")


def get_parser():
    parser = FriendlyParser(
        description="Reads in a file of Newick strings, and outputs a file "
        "with all the median triplet trees."
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
        help="output file (warning: any existing file will be overwritten!)."
        " Defaults to out_<input file>",
        default=None,
    )
    add_common_arguments(parser)
    parser.add_argument(
        "-t",
        "--threads",
        action="store",
        type=int,
        default=-1,
        help="maximum number of concurrent threads (defaults to number of "
        "CPUs, or 1 if undetermined). Must be a positive integer or -1 "
        "for the default guess",
    )
    parser.add_argument(
        "--novalidate",
        action="store_true",
        help="don't perform line-by-line sanity check for each input Newick"
        + " string (for a small speedup)",
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
        help="print the median trees to stdout",
        default=False,
    )
    parser.add_argument(
        "-b",
        "--binary",
        action="store",
        type=str,
        help="save the weights array to a binary file. This file can be "
        "used to find additional trees. Traditionally this file has "
        "the extension .p",
    )

    return parser


def main():
    tic = time()

    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.quiet)

    if args.nosave and not args.print:
        parser.error(
            "--nosave cannot be used without --print, otherwise the output goes nowhere"
        )
    if not (args.threads >= 1 or args.threads == -1):
        parser.error("the number of threads must be a positive integer or -1")

    in_file = args.i
    out_file = args.o if args.o is not None else "out_" + basename(in_file)
    n_threads = args.threads if args.threads != -1 else (cpu_count() or 1)
    print_trees = args.print

    log.info(style("Input parameters:", UNDERLINE))
    log.info("Newick file: %s", in_file)
    if args.nosave:
        log.info("Output file: outputting to stdout instead.")
    else:
        log.info("Output file: %s", out_file)
    log.info("Max threads: %d", n_threads)
    if args.novalidate:
        log.info("Not validating Newick strings!")
    log.info("")

    log.info(style("Parsing input text file.", UNDERLINE))
    try:
        with open(in_file) as f:
            log.info("* Stripping Newick strings.")
            lines = [line.strip() for line in f]
    except OSError:
        log.error("Can't open input file %s for reading. Aborting.", in_file)
        return 1

    # Skip blank lines and comments (lines starting with #), keeping line
    # numbers for error messages.
    numbered = [(i + 1, s) for i, s in enumerate(lines) if s and s[0] != "#"]

    if not args.novalidate:
        log.info("* Checking for matching parentheses and semicolon in each GT.")
        for line_no, s in numbered:
            # Need to put in a stricter validator here
            if s[-1] != ";":
                log.error("Line %d doesn't end with a semicolon! Aborting!", line_no)
                return 1
            if s.count("(") != s.count(")"):
                log.error(
                    "Line %d doesn't have an equal number of left and right "
                    "brackets! Aborting!",
                    line_no,
                )
                return 1

    nwks = [s for _, s in numbered]
    if not nwks:
        log.error("No Newick strings found in %s. Aborting.", in_file)
        return 1

    log.info("")
    log.info(style("Finding median tree. This might take a while!", UNDERLINE))
    (
        median_nwks,
        reverse_dictionary,
        triplet_weights,
        stack,
        best_biparts,
    ) = median_triplet_trees(nwks, n_threads=n_threads, return_extra=True)

    log.info("")
    log.info(style("Done!", BOLD, UNDERLINE))
    if not args.nosave:
        try:
            with open(out_file, "w") as f:
                f.writelines(s + "\n" for s in median_nwks)
            log.info(
                "* %s%s.",
                style("Wrote all median triplet trees to ", BOLD),
                style(out_file, BOLD, ITALICS),
            )
        except OSError:
            log.error("Can't write to %s. Outputting to stdout instead.", out_file)
            # If we can't write to the file, print the trees as a last resort.
            print_trees = True

    log.info("🤖💬 Beep boop, finished in %.2f seconds.", time() - tic)

    # The results: the only thing written to stdout.
    if print_trees:
        for s in median_nwks:
            print(s)

    if args.binary is not None:
        try:
            save_weights(
                args.binary,
                version=mtrip.__version__,
                nwks=nwks,
                median_nwks=median_nwks,
                reverse_dictionary=reverse_dictionary,
                triplet_weights=triplet_weights,
                stack=stack,
                best_biparts=best_biparts,
            )
        except OSError:
            log.error(
                "Can't write to %s. Aborting serializing the processed data.",
                args.binary,
            )
            return 1
        log.info(
            "* %s%s. 🥒🏋️",
            style("Pickled weights to ", BOLD),
            style(args.binary, BOLD, ITALICS),
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
