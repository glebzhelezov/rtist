import itertools
import logging
import random
import sys
import textwrap

from mtrip.bitsnbobs import get_binary_subsets, init_bipart_rep_function, popcount
from mtrip.cli._common import (
    BOLD,
    ITALICS,
    UNDERLINE,
    FriendlyParser,
    WeightsFileError,
    add_common_arguments,
    load_weights,
    pickle_warning,
    setup_logging,
    style,
)

log = logging.getLogger("mtrip.cli")


def get_biparts(x):
    """These are just the pairs where a < x-a and x&a=0"""
    return [(a, x - a) for a in get_binary_subsets(x) if 2 * a < x]


def get_candidates(
    triplet_weights,
    stack,
    reverse_dictionary,
    min_score,
    n_trees,
    n_burnin,
    seed=0,
):
    rng = random.Random(seed)
    n_species = len(reverse_dictionary)
    universe = 2**n_species - 1
    # This is a function which maps (a,b) to the base-3 representation
    bipart_rep = init_bipart_rep_function(n_species)

    # Just a shorthand for checking if (a,b) can give us a sufficient weight
    def maximal_val(a, b):
        return triplet_weights[bipart_rep(a, b)] + stack[a] + stack[b]

    log.info("* Finding initial splits")
    # > Find the topmost splits
    # These are the topmost splits
    candidates = [
        {
            "curscore": triplet_weights[bipart_rep(a, b)],
            "biparts": {a + b: (a, b)},
            "active": [],
        }
        for (a, b) in get_biparts(2**n_species - 1)
        if maximal_val(a, b) >= min_score
    ]

    finished_candidates = []
    # This is a placeholder for all the active (i.e. can be split) candidates
    new_candidates = []

    for candidate in candidates:
        for x in candidate["biparts"][universe]:
            if popcount(x) > 2:
                candidate["active"].append(x)

        if len(candidate["active"]) > 0:
            new_candidates.append(candidate)
        else:
            finished_candidates.append(candidate)

    # We only want to propagate the active candidates; this should be all
    # of them unless the trees are very small, or we have candidates with
    # extra depth levels (i.e. have been preprocessed somewhere, maybe in
    # future versions of this code).
    candidates = new_candidates

    # Burn in
    log.info("* Beginning burn-in")
    while (
        len(candidates) != 0 and len(candidates) + len(finished_candidates) < n_burnin
    ):
        # We'll fill this up with the new splits
        new_candidates = []

        for candidate in candidates:
            # Look at every possible combo of subpartitions
            potential_splits = itertools.product(
                *(get_biparts(x) for x in candidate["active"])
            )
            # Choose only the ones which could possibly satisfy our constraint
            possible_splits = list(
                x
                for x in potential_splits
                if sum(maximal_val(a, b) for (a, b) in x)
                >= min_score - candidate["curscore"]
            )
            # Now add this list of possible splits and continue processing them

            for splits in possible_splits:
                new_candidate = dict()
                new_candidate["curscore"] = candidate["curscore"]
                new_candidate["biparts"] = candidate["biparts"].copy()
                new_candidate["active"] = []

                for a, b in splits:
                    new_candidate["curscore"] += triplet_weights[bipart_rep(a, b)]
                    new_candidate["biparts"][a + b] = (a, b)
                    for x in (a, b):
                        if popcount(x) > 2:
                            new_candidate["active"].append(x)

                if len(new_candidate["active"]) > 0:
                    new_candidates.append(new_candidate)
                    # Stop if we've gathered enough
                    if len(new_candidates) + len(finished_candidates) >= n_burnin:
                        break
                # This shouldn't happen if all the candidates were initialized
                # at the same time + the constants are reasonable
                else:
                    finished_candidates.append(new_candidate)
                    # Stop if we've gathered enough
                    if len(new_candidates) + len(finished_candidates) >= n_burnin:
                        break
                # This shouldn't happen if all the candidates were initialized
                # at the same time + the constants are reasonable
                # Stop if we've gathered enough
                if len(new_candidates) + len(finished_candidates) >= n_burnin:
                    break
            # This shouldn't happen if all the candidates were initialized at
            # the same time + the constants are reasonable
            # Stop if we've gathered enough
            if len(new_candidates) + len(finished_candidates) >= n_burnin:
                break

        # Update the list of candidates
        candidates = new_candidates.copy()
        if len(candidates) + len(finished_candidates) >= n_burnin:
            break

    # Now we take a random walk along each started path; choose the starting
    # paths uniformly
    n_candidates = len(candidates) + len(finished_candidates)
    if n_candidates < n_trees:
        log.info(
            textwrap.fill(
                f"* Could only find {n_candidates} trees satisfying the "
                f"constraint ({n_trees} requested)"
            )
        )
        chosen_paths = candidates + finished_candidates
    else:
        log.info("* Picking random subset of tree candidates")
        chosen_paths = rng.choices(
            candidates + finished_candidates,
            k=n_trees,
        )

    # Fully split-up the remaining candidates

    # These are all guaranteed to work out, so let's go through them,
    # choosing random splits along the way.
    log.info("* Refining all splits")
    for candidate in chosen_paths:
        while len(candidate["active"]) != 0:
            # Look at every possible combo of subpartitions
            potential_splits = itertools.product(
                *(get_biparts(x) for x in candidate["active"])
            )
            # Choose only the ones which could possibly satisfy our constraint
            possible_splits = list(
                x
                for x in potential_splits
                if sum(maximal_val(a, b) for (a, b) in x)
                >= min_score - candidate["curscore"]
            )
            chosen_splits = rng.choice(possible_splits)
            candidate["active"] = []
            for a, b in chosen_splits:
                candidate["curscore"] += triplet_weights[bipart_rep(a, b)]
                candidate["biparts"][a + b] = (a, b)
                for x in (a, b):
                    if popcount(x) > 2:
                        candidate["active"].append(x)

    # We're done! Return for outputting.
    return chosen_paths


def get_present_species(x, reverse_dictionary):
    """Find the names of all the species in the set with
    bit representation x.

    x - bitwise representation of a set of labels
    reverse_dictionary - dictionary sending a set x to bipart (a,b),
    where x, a, b are given as binary numbers and a<b."""
    return [
        reverse_dictionary[i]
        for i in range(len(reverse_dictionary))
        if x & (2**i) == 2**i
    ]


def _get_nwk(x, reverse_dictionary, biparts):
    if popcount(x) == 1:
        names = get_present_species(x, reverse_dictionary)
        nwk = names[0]
    elif popcount(x) == 2:
        names = get_present_species(x, reverse_dictionary)
        nwk = "({},{})".format(*names)
    else:
        (a, b) = biparts[x]
        a_tree = _get_nwk(a, reverse_dictionary, biparts)
        b_tree = _get_nwk(b, reverse_dictionary, biparts)

        nwk = f"({a_tree},{b_tree})"

    return nwk


def get_nwk(x, reverse_dictionary, biparts):
    """Build up a Newick string recursively, given by bipartitions.

    x - bit representation of the set of species involved (usually
        2^n_species-1)
    reverse_dictionary - list of names s.t. ith set bit corresponds to
                         this name
    biparts - dictionary sending a set x to bipart (a,b), where x, a, b
              are given as binary numbers and a<b.
    """
    return _get_nwk(x, reverse_dictionary, biparts) + ";"


def get_parser():
    parser = FriendlyParser(
        description="Takes a pickled (serialized) weights file, and outputs "
        "trees with suboptimal scores that are greater than a set minimum. "
        "The output is sorted in descending score order, and each tree's "
        "score is in commented-out line above the Newick string."
    )
    parser.add_argument(
        "i",
        action="store",
        type=str,
        help="input pickled weights file (e.g. weights.p), produced by the "
        "mediantriplet utility with the -b flag",
    )
    parser.add_argument(
        "o",
        nargs="?",
        action="store",
        type=str,
        help="output file (warning: any existing file will be overwritten!). "
        "If no argument is given, output is written to stdout",
        default=None,
    )
    parser.add_argument(
        "-p",
        "--print",
        action="store_true",
        help="also print the trees to stdout when writing an output file",
        default=False,
    )

    parser.add_argument(
        "-m",
        "--minscore",
        action="store",
        type=int,
        help="each tree must have a score greater than or equal to this",
        default=-1,
    )
    parser.add_argument(
        "-f",
        "--fraction",
        action="store",
        type=float,
        help="each tree must have a score that's at least this fraction of "
        "the maximal score. Must be greater than 0 and less than or equal "
        "to 1. Defaults to 0.99",
        default=0.99,
    )
    parser.add_argument(
        "-n",
        "--ntrees",
        type=int,
        help="output at most this many trees. Defaults to 100",
        default=100,
    )
    parser.add_argument(
        "-b",
        "--burnin",
        type=int,
        help="find this many viable candidates (i.e. find finer splits) "
        "before randomly choosing a subsample. A higher value gives a more "
        "uniform distribution, but takes more time and memory. Defaults to "
        "4x the number of requested trees",
        default=None,
    )
    parser.add_argument(
        "-s",
        "--seed",
        type=int,
        help="seed for the random number generator used in taking a random "
        "walk along the space of splits. Defaults to 0",
        default=0,
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        default=False,
        help="don't ask for confirmation to load a pickle file",
    )
    add_common_arguments(parser)

    return parser


def main():
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.quiet)

    if args.minscore != -1 and args.minscore < 0:
        parser.error("invalid minimum score")
    if not 0 < args.fraction <= 1:
        parser.error("invalid minimum fraction")
    if not args.ntrees > 0:
        parser.error("invalid number of requested trees")
    if args.burnin is None:
        args.burnin = 4 * args.ntrees
    if args.burnin < args.ntrees:
        parser.error("burnin number less than requested number of trees")
    # Without an output file, the trees go to stdout.
    print_trees = args.print or args.o is None

    log.info(style("Input parameters:", UNDERLINE))
    log.info("Input file  : %s", args.i)
    if args.o is not None:
        log.info("Output file : %s", args.o)
    else:
        log.info("Output file : outputting to stdout instead")
    log.info("Use stdout  : %s", print_trees)
    if args.minscore != -1:
        log.info("Min score   : %d", args.minscore)
    if args.fraction != 1:
        log.info("Min fraction: %s", args.fraction)
    log.info("Max n trees : %d", args.ntrees)
    log.info("Burnin count: %d", args.burnin)
    log.info("RNG seed    : %d", args.seed)

    # Warn the user about the pickle, it is the moral thing to do!
    if not args.yes:
        print(file=sys.stderr)
        pickle_warning(args.i)

    log.info("")
    log.info(style("Processing pickle", UNDERLINE))
    log.info("* Loading and verifying pickle")
    try:
        unpickled = load_weights(args.i)
    except WeightsFileError as e:
        log.error("%s Aborting.", e)
        return 1

    log.info("File was created using version %s of the utility.", unpickled["version"])
    reverse_dictionary = unpickled["reverse_dictionary"]
    triplet_weights = unpickled["triplet_weights"]
    stack = unpickled["stack"]

    # Figure out the min score
    n_species = len(reverse_dictionary)
    max_score = stack[2**n_species - 1]
    log.info("Data for %d species and maximum triplet score %d.", n_species, max_score)
    # Choose the greater of the two possible score cutoffs; if minscore
    # was not set then it's equal to -1 and is overwritten by the fraction.
    min_score = int(max(args.fraction * max_score, args.minscore))
    log.info(
        textwrap.fill(
            f"* Setting minimum viable tree score to {min_score} "
            "(max of -m and -f flags)"
        )
    )

    log.info("")
    log.info(style("Finding trees", UNDERLINE))
    solution = get_candidates(
        triplet_weights,
        stack,
        reverse_dictionary,
        min_score,
        args.ntrees,
        args.burnin,
        seed=args.seed,
    )
    log.info("* Sorting by score")
    solution.sort(key=lambda x: x["curscore"], reverse=True)

    log.info("")
    log.info(style("Done!", BOLD, UNDERLINE))
    log.info(
        style(f"Found {len(solution)} trees satisfying the given constraints. 🪆", BOLD)
    )
    # Each tree is preceded by a comment line with its score.
    log.info("* Translating to Newick format")
    universe = 2**n_species - 1
    lines = []
    for candidate in solution:
        lines.append(f"#{candidate['curscore']}")
        lines.append(get_nwk(universe, reverse_dictionary, candidate["biparts"]))

    if args.o is not None:
        try:
            with open(args.o, "w") as f:
                f.writelines(s + "\n" for s in lines)
            log.info(
                "* %s%s.",
                style("Wrote all found trees to ", BOLD),
                style(args.o, BOLD, ITALICS),
            )
        except OSError:
            log.error("Could not write to %s. Outputting to stdout instead.", args.o)
            print_trees = True

    # The results: the only thing written to stdout.
    if print_trees:
        log.info("* Writing output to stdout.")
        for s in lines:
            print(s)

    return 0


if __name__ == "__main__":
    sys.exit(main())
