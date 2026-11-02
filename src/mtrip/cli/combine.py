import logging
import sys
from os.path import exists

from mtrip import __version__
from mtrip import median_tree_reconstruction as mtr
from mtrip.cli._common import (
    FriendlyParser,
    WeightsFileError,
    add_common_arguments,
    load_weights,
    save_weights,
    setup_logging,
)

log = logging.getLogger("mtrip.cli")


def get_parser():
    parser = FriendlyParser(
        description="Combines weight pickles produced by mtrip -b (for example, "
        "from separate runs on parts of a data set) into one, and finds the "
        "median trees of the combined data. All inputs must have the same "
        "species labels."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        metavar="in_pickle.p",
        help="weight pickles to combine (at least two)",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="output pickle (warning: any existing file will be overwritten!). "
        "Defaults to combined_weights.p, or combined_weights_<n>.p if that "
        "already exists",
    )
    add_common_arguments(parser)
    return parser


def default_output_name(basename="combined_weights"):
    """basename.p, or basename_<n>.p for the first n that doesn't exist."""
    if not exists(basename + ".p"):
        return basename + ".p"
    suffix = 1
    while exists(f"{basename}_{suffix}.p"):
        suffix += 1
    return f"{basename}_{suffix}.p"


def main():
    parser = get_parser()
    args = parser.parse_args()
    setup_logging(args.quiet)
    if len(args.inputs) < 2:
        parser.error("at least two pickle files are needed to combine")

    try:
        first = load_weights(args.inputs[0])
    except WeightsFileError as e:
        log.error("%s: %s Aborting.", args.inputs[0], e)
        return 1
    main_reverse_dictionary = first["reverse_dictionary"]
    main_weights = first["triplet_weights"]
    main_nwks = first["nwks"]
    n_species = len(main_reverse_dictionary)

    for filename in args.inputs[1:]:
        try:
            data = load_weights(filename)
        except WeightsFileError as e:
            log.error("%s: %s Aborting.", filename, e)
            return 1
        if data["reverse_dictionary"] != main_reverse_dictionary:
            log.error("%s: not the same species labels! Aborting.", filename)
            return 1
        weights = data["triplet_weights"]
        if len(weights) != len(main_weights):
            log.error("%s: weights array has the wrong length! Aborting.", filename)
            return 1
        log.info("Adding weight contributions of %s.", filename)
        for i in range(len(main_weights)):
            main_weights[i] += weights[i]
        main_nwks += data["nwks"]

    log.info("Computing stack")
    main_stack, main_best_biparts = mtr.get_stack(main_weights, n_species)
    log.info("Finding the median trees")
    main_trees = mtr.get_all_trees(
        2**n_species - 1, main_reverse_dictionary, main_best_biparts
    )

    output = args.output if args.output is not None else default_output_name()
    try:
        save_weights(
            output,
            version="combined_" + __version__,
            nwks=main_nwks,
            median_nwks=main_trees,
            reverse_dictionary=main_reverse_dictionary,
            triplet_weights=main_weights,
            stack=main_stack,
            best_biparts=main_best_biparts,
        )
    except OSError as e:
        log.error("Failed to write combined weights pickle: %s", e)
        return 1
    log.info("Wrote combined weights pickle to %s.", output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
