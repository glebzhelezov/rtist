#pyximport.install(language_level=3)

#import pyximport
import re
import comb2
#import numpy as np

#from gmpy2 import popcount
from bitsnbobs import popcount, get_binary_subsets, init_bipart_rep_function
import snoob
#from triplet import triplet_cy

def simplify_nwk(s):
    """Returns Newick representation with only leaf names."""
    # Get rid of spaces at the start and end
    s = s.strip()
    s = s.replace(" ", "")
    # Get rid of non-leaf names
    s = re.sub(r"\)[^,)]+", ")", s)
    # Get rid of branch lengths
    s = re.sub(r":[0-9]*[.]?[0-9]*", "", s)

    return s


def get_names(gts_nwks):
    """Gets the unique names in a list of Newick strings."""
    names = set([])
    for i, gt_nwk in enumerate(gts_nwks):
        tokens = re.findall(r"([(,])([a-zA-Z0-9]*)(?::\d*(\.\d*)?)?(?=[,)])", gt_nwk)
        cur_names = [t[1] for t in tokens]
        if "" in cur_names:
            raise SyntaxError(
                "Unlabeled tip in Newick string on line {}!".format(i + 1)
            )
        names.update(cur_names)
        # parse(gt_nwk)
        # get_names(gts_nwk)

    names_list = list(names)
    # names_list.sort()
    dictionary = {names_list[i]: i for i in range(len(names_list))}
    reverse_dictionary = names_list.copy()

    return names, dictionary, reverse_dictionary


def splitter(nwk):
    s = nwk
    bracket_count = 0
    start_position = 0

    if s[0] != "(":
        return tuple([s])

    for i, ch in enumerate(s):
        if ch == "(":
            bracket_count += 1
        elif ch == ")":
            bracket_count -= 1
        elif ch == ",":
            if bracket_count == 1:
                left = s[start_position + 1 : i]
                right = s[i + 1 : -1]

                return left, right


def get_biparts(nwk, dictionary):
    biparts = []

    def recurse(s):
        split = splitter(s)

        if len(split) == 1:
            return 2 ** dictionary[split[0]]
        if len(split) == 2:
            a = recurse(split[0])
            b = recurse(split[1])

            biparts.append((min(a, b), max(a, b)))
            return a + b

    # fill up the biparts list
    recurse(nwk)

    return biparts


def get_weights(gts_nwks, dictionary):
    weights = {}
    for s in gts_nwks:
        biparts = get_biparts(s, dictionary)

        for bipart in biparts:
            if bipart in weights:
                weights[bipart] += 1
            else:
                weights[bipart] = 1

    return weights


def get_stack(bipartition_weights, n_species):
    # The "stack" gives the best weight of each subset
    f = init_bipart_rep_function(n_species)
    # Score of each triple
    stack = comb2.zero_array(2**n_species, 'i')
    #stack = np.zeros(2 ** n_species, dtype=np.intc)
    # Each subset has a list of the maximizing bipartitions
    best_biparts = [[] for _ in range(2 ** n_species)]

    universe = 2 ** n_species - 1

    # Fill up the stack
    for n in range(3, n_species + 1):
        for combo in snoob.get_all_snoobs(universe, n):
            best_bipart_list = best_biparts[combo]
            max_score = -1
            for subset in get_binary_subsets(combo):
                complement = combo - subset
                if subset < complement:
                    score = (
                        bipartition_weights[f(subset, complement)]
                        + stack[subset]
                        + stack[complement]
                    )
                    if score == max_score:
                        best_bipart_list.append((subset, complement))
                    elif score > max_score:
                        max_score = score
                        best_bipart_list.clear()
                        best_bipart_list.append((subset, complement))
            # print('updating', combo)
            # best_bipart[combo] = max_bipart
            stack[combo] = max_score

    return stack, best_biparts


def process_nwks(nwks, n_threads=1):
    """Returns weights of bipartitions, dictionary, and reverse dictionary"""
    # Get rid of unnecessary info in Newick string
    nwks_simplified = [simplify_nwk(s) for s in nwks]
    # Map each name to an integer
    names, dictionary, reverse_dictionary = get_names(nwks_simplified)
    # Get the weights of the bipartitions in the GTs
    weights = get_weights(nwks_simplified, dictionary)
    # Get the number of species across all the GTs
    n_species = len(names)
    # Get the weights of all possible bipartitions
    triplet_weights = comb2.py_compressed_weight_rep(
        weights, n_species, n_threads=n_threads
    )

    return triplet_weights, dictionary, reverse_dictionary


def get_present_species(x, reverse_dictionary):
    # Can be optimized with bitwise operations
    return [
        reverse_dictionary[i]
        for i in range(len(reverse_dictionary))
        if x & (2 ** i) == 2 ** i
    ]


def _get_all_trees(x, dictionary, reverse_dictionary, best_biparts):
    all_trees = []
    if popcount(x) == 1:
        names = get_present_species(x, reverse_dictionary)
        all_trees.append(names[0])
    elif popcount(x) == 2:
        names = get_present_species(x, reverse_dictionary)
        all_trees.append("({},{})".format(*names))
    else:
        for (a, b) in best_biparts[x]:
            a_trees = _get_all_trees(a, dictionary, reverse_dictionary, best_biparts)
            b_trees = _get_all_trees(b, dictionary, reverse_dictionary, best_biparts)

            for a_prime in a_trees:
                for b_prime in b_trees:
                    all_trees.append("({},{})".format(a_prime, b_prime))

    return all_trees


def get_all_trees(x, dictionary, reverse_dictionary, best_biparts):
    return [
        t + ";" for t in _get_all_trees(x, dictionary, reverse_dictionary, best_biparts)
    ]


def median_triplet_trees(nwks, n_threads=1):
    triplet_weights, dictionary, reverse_dictionary = process_nwks(
        nwks, n_threads=n_threads
    )
    stack, best_biparts = get_stack(triplet_weights, len(dictionary))
    # bitset representation of all the tips
    x = 2 ** len(reverse_dictionary) - 1
    print(stack[x])
    return get_all_trees(x, dictionary, reverse_dictionary, best_biparts)
