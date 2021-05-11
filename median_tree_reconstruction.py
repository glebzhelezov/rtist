import re
import triplet_omp
import snoob
from bitsnbobs import popcount, get_binary_subsets, init_bipart_rep_function


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
        tokens = re.findall(
            r"([(,])([a-zA-Z0-9]*)(?::\d*(\.\d*)?)?(?=[,)])", gt_nwk
        )
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
    """Returns the two inner Newick subtrees; assumes Newick string does not
    end with a semicolon."""
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
    """Get all the bipartitions in the Newick tree. Each partition is
    represented by pairs of binary numbers. The smaller binary number is the
    first coordinate."""
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

def get_subset_biparts(nwks, dictionary):
    biparts = []
    biparts_per_subset = dict([])

    def recurse(s):
        split = splitter(s)

        if len(split) == 1:
            return 2 ** dictionary[split[0]]
        if len(split) == 2:
            a = recurse(split[0])
            b = recurse(split[1])

            subset = a+b
            bipart = (min(a,b), max(a,b))
            #biparts.append(bipart)

            # List this bipart as belonging to the partition
            if subset in biparts_per_subset:
                #print(subset)
                if bipart not in biparts_per_subset[subset]:
                    biparts_per_subset[subset].append(bipart)
            else:
                #print(subset)
                biparts_per_subset[subset] = [bipart]
            
            return subset

    # fill up the biparts list
    for nwk in nwks:
        recurse(nwk)

    return biparts_per_subset

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
    print("* Finding maximal possible weight of each bipartition.")
    # The "stack" gives the best weight of each subset
    f = init_bipart_rep_function(n_species)
    # Score of each triple
    stack = triplet_omp.zero_array(2 ** n_species, "i")
    # stack = np.zeros(2 ** n_species, dtype=np.intc)
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
    """Returns weights of bipartitions, dictionary, and reverse dictionary
    
    Input:
    nwks - list of Newick strings
    n_threads - n threads to use (default=1)"""
    print("* Parsing Newick strings and recording bipartitions in GTs.")
    # Get rid of unnecessary info in Newick string
    nwks_simplified = [simplify_nwk(s) for s in nwks]
    # Map each name to an integer
    names, dictionary, reverse_dictionary = get_names(nwks_simplified)
    # Get the number of species across all the GTs
    n_species = len(names)
    # Warn user of impeding doom; this is a pretty low bar though, 20 is more
    # reasonable on modern hardware.
    if n_species > 15:
        print(
            "Warning: attempting to find exact tree with {} tips. The computation might run out of memory, or take an unreasonable amount of time.".format(
                n_species
            )
        )
    
    # Get the weights of the bipartitions in the GTs
    weights = get_weights(nwks_simplified, dictionary)
    # Get the biparts by the subset (i.e. (a+b)->[(a,b),...]
    biparts_by_subset = get_subset_biparts(nwks_simplified, dictionary)
    # Arrange data to be easily accessible by C code
    subsets = []
    start_i = []
    end_i = []
    biparts_a = []
    biparts_b = []
    bipart_weights = []

    position = 0
    for subset in biparts_by_subset.keys():
        subsets.append(subset)
        start_i.append(position)
        biparts = biparts_by_subset[subset]
        for (a,b) in biparts:
            biparts_a.append(a)
            biparts_b.append(b)
            bipart_weights.append(weights[(a,b)])
            position += 1
        end_i.append(position)
    # Get the weights of all possible bipartitions
    print("* Finding each possible bipartition's weight:")
    triplet_weights = triplet_omp.py_compressed_weight_rep(
            subsets, start_i, end_i, biparts_a, biparts_b, bipart_weights,
            n_species, n_threads=n_threads)
    print("Done!")

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
            a_trees = _get_all_trees(
                a, dictionary, reverse_dictionary, best_biparts
            )
            b_trees = _get_all_trees(
                b, dictionary, reverse_dictionary, best_biparts
            )

            for a_prime in a_trees:
                for b_prime in b_trees:
                    all_trees.append("({},{})".format(a_prime, b_prime))

    return all_trees


def get_all_trees(x, dictionary, reverse_dictionary, best_biparts):
    return [
        t + ";"
        for t in _get_all_trees(x, dictionary, reverse_dictionary, best_biparts)
        ]

def median_triplet_trees(nwks, n_threads=1):
    triplet_weights, dictionary, reverse_dictionary = process_nwks(
        nwks, n_threads=n_threads
    )

    stack, best_biparts = get_stack(triplet_weights, len(dictionary))
    # bitset representation of all the tips
    x = 2 ** len(reverse_dictionary) - 1
    n = len(dictionary)
    # This assumes each GT has all the species, so this is actually not a
    # sharp upper bound!
    theoretical_bound = len(nwks) * n * (n - 1) * (n - 2) // 6
    print(
        "Best possible triplet count is {}, out of a maximum of {}.".format(
            stack[x], theoretical_bound
        )
    )
    return get_all_trees(x, dictionary, reverse_dictionary, best_biparts)
