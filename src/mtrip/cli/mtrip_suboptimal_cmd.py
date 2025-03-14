#!/usr/bin/env python
import argparse
import itertools
import pickle
import random
import sys
import textwrap

from mtrip import __version__
from mtrip.bitsnbobs import (get_binary_subsets, init_bipart_rep_function,
                             popcount)

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


def pickle_warning(filename):
    print(bold + "From the Python 3 manual:" + end)
    s = (
        "Only unpickle data you trust. It is possible to construct "
        "malicious pickle data which will execute arbitrary code during "
        "unpickling. Never unpickle data that could have come from an "
        "untrusted source, or that could have been tampered with."
    )
    print(textwrap.fill(s))
    print()
    s = (
        "You can avoid this interactive warning in the future "
        "by using the -y flag."
    )
    print(textwrap.fill(s))
    print()

    verification = ""

    while verification not in {"y", "n"}:
        verification = input(
            "Load the file {}{}{}? (y/n) ".format(bold, filename, end)
        )
        verification = verification.lower().strip()

    if verification == "n":
        print("Aborting.")
        sys.exit(0)


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
    universe = 2 ** n_species - 1
    # This is a function which maps (a,b) to the base-3 representation
    bipart_rep = init_bipart_rep_function(n_species)

    # Just a shorthand for checking if (a,b) can give us a sufficient weight
    def maximal_val(a, b):
        return triplet_weights[bipart_rep(a, b)] + stack[a] + stack[b]

    print("* Finding initial splits")
    # > Find the topmost splits
    # These are the topmost splits
    candidates = [
        {
            "curscore": triplet_weights[bipart_rep(a, b)],
            "biparts": {a + b: (a, b)},
            "active": [],
        }
        for (a, b) in get_biparts(2 ** n_species - 1)
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
    print("* Beginning burn-in")
    while (
        len(candidates) != 0
        and len(candidates) + len(finished_candidates) < n_burnin
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
                (
                    x
                    for x in potential_splits
                    if sum(maximal_val(a, b) for (a, b) in x)
                    >= min_score - candidate["curscore"]
                )
            )
            # Now add this list of possible splits and continue processing them

            for splits in possible_splits:
                new_candidate = dict()
                new_candidate["curscore"] = candidate["curscore"]
                new_candidate["biparts"] = candidate["biparts"].copy()
                new_candidate["active"] = []

                for (a, b) in splits:
                    new_candidate["curscore"] += triplet_weights[
                        bipart_rep(a, b)
                    ]
                    new_candidate["biparts"][a + b] = (a, b)
                    for x in (a, b):
                        if popcount(x) > 2:
                            new_candidate["active"].append(x)

                if len(new_candidate["active"]) > 0:
                    new_candidates.append(new_candidate)
                    # Stop if we've gathered enough
                    if (
                        len(new_candidates) + len(finished_candidates)
                        >= n_burnin
                    ):
                        break
                # This shouldn't happen if all the candidates were initialized
                # at the same time + the constants are reasonable
                else:
                    finished_candidates.append(new_candidate)
                    # Stop if we've gathered enough
                    if (
                        len(new_candidates) + len(finished_candidates)
                        >= n_burnin
                    ):
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
        print(
            textwrap.fill(
                "* Could only find {} trees satisfying the constraint ({} "
                "requested)".format(n_candidates, n_trees)
            )
        )
        chosen_paths = candidates + finished_candidates
    else:
        print("* Picking random subset of tree candidates")
        chosen_paths = rng.choices(
            candidates + finished_candidates, k=n_trees,
        )

    # Fully split-up the remaining candidates

    # These are all guaranteed to work out, so let's go through them,
    # choosing random splits along the way.
    print("* Refining all splits")
    for candidate in chosen_paths:
        while len(candidate["active"]) != 0:
            # Look at every possible combo of subpartitions
            potential_splits = itertools.product(
                *(get_biparts(x) for x in candidate["active"])
            )
            # Choose only the ones which could possibly satisfy our constraint
            possible_splits = list(
                (
                    x
                    for x in potential_splits
                    if sum(maximal_val(a, b) for (a, b) in x)
                    >= min_score - candidate["curscore"]
                )
            )
            chosen_splits = rng.choice(possible_splits)
            candidate["active"] = []
            for (a, b) in chosen_splits:
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
        if x & (2 ** i) == 2 ** i
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

        nwk = "({},{})".format(a_tree, b_tree)

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
        help="print the output to the screen",
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
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=__version__,
    )

    return parser


def main():
    parser = get_parser()
    cli_flags = parser.parse_args()

    print(underline + "Input parameters:" + end)
    print("Input file  : {}".format(cli_flags.i))
    if cli_flags.o is not None:
        print("Output file : {}".format(cli_flags.o))
    else:
        print("Output file : outputting to stdout instead")
        cli_flags.print = True
    print("Use stdout  :", cli_flags.print)
    if cli_flags.minscore != -1:
        if cli_flags.minscore < 0:
            print("Invalid minimum score. Aborting.")
            return 1
        print("Min score   :", cli_flags.minscore)
    if cli_flags.fraction != 1:
        if not 0 < cli_flags.fraction <= 1:
            print("Invalid minimum fraction. Aborting.")
            return 1
        print("Min fraction:", cli_flags.fraction)
    if not cli_flags.ntrees > 0:
        print("Invalid number of requested trees. Aborting.")
        return 1
    print("Max n trees :", cli_flags.ntrees)
    if cli_flags.burnin is None:
        cli_flags.burnin = 4 * cli_flags.ntrees
    if cli_flags.burnin < cli_flags.ntrees:
        print("Burnin number less than requested number of trees. Aborting.")
        return
    print("Burnin count:", cli_flags.burnin)
    print("RNG seed    :", cli_flags.seed)

    # Warn the user about the pickle, it is the moral thing to do!
    if not cli_flags.yes:
        print()
        pickle_warning(cli_flags.i)

    print()
    print(underline + "Processing pickle" + end)
    try:
        with open(cli_flags.i, "rb") as f:
            print("* Loading pickle")
            try:
                unpickled = pickle.load(f)
            except (pickle.UnpicklingError, EOFError) as e:
                print(e)
                print("Can't unpickle (wrong file?). Aborting.")
                return 1
    except OSError:
        print(
            "Can't open input file {} for reading. Aborting.".format(
                cli_flags.i
            )
        )
        return 1

    print("* Verifying")
    # This is just to lower the probability of a nonsense file--not actually
    # for any kind of security, etc.
    try:
        if unpickled["abigsecret"] != "ogurets":
            print("This does not seem to be a valid file. Aborting.")
            return 1
    except Exception:
        print("This does not seem to be a valid file. Aborting.")
        return 1

    print(
        "File was created using version {} of the utility.".format(
            unpickled["version"]
        )
    )
    keys = ["reverse_dictionary", "triplet_weights", "stack"]
    reverse_dictionary, triplet_weights, stack = (unpickled[k] for k in keys)

    # Figure out the min score
    n_species = len(reverse_dictionary)
    max_score = stack[2 ** n_species - 1]
    print(
        "Data for {} species and maximum triplet score {}.".format(
            n_species, max_score
        )
    )
    # Choose the greater of the two possible score cutoffs; if minscore
    # was not set then it's equal to -1 and is overwritten by the fraction. */
    min_score = int(max(cli_flags.fraction * max_score, cli_flags.minscore))
    print(
        textwrap.fill(
            "* Setting minimum viable tree score to {} "
            "(max of -m and -f flags)".format(min_score)
        )
    )

    print()
    print(underline + "Finding trees" + end)
    # Get the solution
    solution = get_candidates(
        triplet_weights,
        stack,
        reverse_dictionary,
        min_score,
        cli_flags.ntrees,
        cli_flags.burnin,
        seed=cli_flags.seed,
    )
    # Sort of descending score
    print("* Sorting by score")

    print()
    print(bold + underline + "Done!" + end + end)
    success_str = (
        bold
        + "Found {} trees satisfying the given constraints. 🪆".format(
            len(solution)
        )
        + end
    )
    print(success_str)
    solution.sort(key=lambda x: x["curscore"], reverse=True)
    # Record lines to output to screen, file, or both
    print("* Translating to Newick format")
    universe = 2 ** n_species - 1
    lines = []
    for candidate in solution:
        lines.append("#{}".format(candidate["curscore"]))
        lines.append(
            get_nwk(universe, reverse_dictionary, candidate["biparts"])
        )
    if cli_flags.o is not None:
        try:
            with open(cli_flags.o, "w") as f:
                f.writelines([s + "\n" for s in lines])
            print(
                "* {}Wrote all found trees to {}{}{}{}.".format(
                    bold, italics, cli_flags.o, end, end
                )
            )
        except IOError:
            print(
                "Could not write to {}. Outputting to stdout instead.".format(
                    cli_flags.o
                )
            )
            cli_flags.print = True

    if cli_flags.print:
        print("* Writing output to stdout.")
    if cli_flags.print:
        print()
        for s in lines:
            print(s)


if __name__ == "__main__":
    sys.exit(main())