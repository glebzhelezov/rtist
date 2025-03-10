#!/usr/bin/env python

import pickle
import sys
from os import path
from os.path import exists

from mtrip import median_tree_reconstruction as mtr
from mtrip import __version__


def main():
    print("This utility is for combining weight pickles produced by mtrip.")
    print("Usage:\t$ mtrip-combine in_pickle_1.p ... in_pickle_n.p")
    print("The output filename will be printed out at the end of the process.")
    if len(sys.argv) < 2:
        print("Not enough arguments! Exiting.")
        return 1
    elif len(sys.argv) == 2:
        print("Exactly one pickle file given, nothing to combine! Exiting.")
        return 1
    else:
        pickles = sys.argv[1:]

    with open(pickles[0], 'rb') as f:
        in_pickle = pickle.load(f)
        main_reverse_dictionary = in_pickle['reverse_dictionary']
        main_weights = in_pickle['triplet_weights']
        n_species = len(main_reverse_dictionary)
        main_nwks = in_pickle['nwks']

    for filename in pickles[1:]:
        with open(filename, 'rb') as f:
            in_pickle = pickle.load(f)
            reverse_dictionary = in_pickle['reverse_dictionary']
            weights = in_pickle['triplet_weights']
            nwks = in_pickle['nwks']

            if not reverse_dictionary == main_reverse_dictionary:
                print("Not the same species labels! Aborting.")
                return 1
            else:
                print(f"Adding weight contributions of {filename}.")
                for i in range(len(main_weights)):
                    main_weights[i] += weights[i]

                main_nwks += nwks

    print("Computing stack")
    main_stack, main_best_biparts = mtr.get_stack(main_weights, n_species)
    print("Finding the median trees")
    main_trees = mtr.get_all_trees(
            2**n_species-1,
            main_reverse_dictionary,
            main_best_biparts
        )

    out_pickle = {
            'abigsecret':'ogurets',
            'version':'combined_' + __version__,
            'nwks':main_nwks,
            'median_nwks':main_trees,
            'reverse_dictionary':main_reverse_dictionary,
            'triplet_weights':main_weights,
            'stack':main_stack,
            'best_biparts':main_best_biparts,
        }

    # Save to a file without overwriting; should be slicker when not a
    # prototype.
    output_basename = 'combined_weights'

    if exists(output_basename+'.p'):
        suffix = 1
        # Find a filename which doesn't exist
        while exists(f"{output_basename}_{suffix}.p"):
            suffix += 1
        
        output_basename =  f"{output_basename}_{suffix}"
    output_filename = output_basename + '.p'

    try:
        with open(output_filename, 'wb') as f:
            pickle.dump(out_pickle, f)
            print(f"Wrote combined weights pickle to {output_filename}.")
            return 0
    except:
        print("Failed to write combined weights pickle.")
        return 1


if __name__ == "__main__":
    sys.exit(main())