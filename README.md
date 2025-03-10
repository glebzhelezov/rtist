# mtrip

`mtrip` (well, actually, `rtist`--we renamed the command for a laugh before publication, but never renamed the command!) is a package for finding exact median triplet trees.

This work is based on: [*Trying out a million genes to find the perfect pair with RTIST*](https://academic.oup.com/bioinformatics/article/38/14/3565/6596045):

```bibtex
@article{zhelezov2022trying,
  title={Trying out a million genes to find the perfect pair with RTIST},
  author={Zhelezov, Gleb and Degnan, James H},
  journal={Bioinformatics},
  volume={38},
  number={14},
  pages={3565--3573},
  year={2022},
  publisher={Oxford University Press}
}
```

## Installation

From PyPI (recommended):

```bash
$ pip install mtrip
```

From GitHub:

```bash
$ pip install git+https://github.com/glebzhelezov/rtist.git
```

Binary wheels are automatically built for:
- Linux (x86_64)
- macOS (Intel x86_64)
- macOS (Apple Silicon/arm64)

This means no compiler is needed for installation on supported platforms.

## Building from source

### Prerequisites

- CMake (version 3.12 or higher)
- C/C++ compiler (recommended: with OpenMP support)
- Python 3.6 or higher
- Cython 3.0.0 or higher

#### OpenMP on macOS

On macOS, OpenMP support requires installing `libomp` with Homebrew:

```bash
$ brew install libomp
```

### Building and installation

1. Clone the repository:

   ```bash
   $ git clone https://github.com/glebzhelezov/rtist.git
   $ cd rtist
   ```

2. Install using pip (recommended):

   ```bash
   $ pip install -e .
   ```

This will automatically:
- Run CMake to configure the build
- Compile the C extensions (with OpenMP support where available)
- Install the package in development mode

### Building and installation using traditional build process
Alternatively, you can use the traditional build process.

 1. Generate a build script with CMake:    

    ```bash
    $ cmake -B build
    ```

 2. Build C library:

    ```bash
    $ cmake --build build
    ```

 3. Install `mtrip`:

    ```bash
    $ pip install .
    ```

 4. `mtrip` will be available as a command whenever you activate the virtual environment that was used during installation. To verify that this is the case, run:

    ```bash
    $ mtrip -h
    ```

    which should output:

    ```bash
    mtrip -h
    usage: mtrip [-h] [-v] [-t THREADS] [--novalidate] [-n] [-p] [-b BINARY] i [o]
    
    Reads in a file of Newick strings, and outputs a file with all the median triplet trees.
    
    positional arguments:
      i                     input file with one Newick string per line
      o                     output file (warning: any existing file will be overwritten!). Defaults to out_<input file>
    
    options:
      -h, --help            show this help message and exit
      -v, --version         show program's version number and exit
      -t, --threads THREADS
                            maximum number of concurrent threads (defaults to number of CPUs, or 1 if undetermined). Must be a positive integer or
                            -1 for the default guess
      --novalidate          don't perform line-by-line sanity check for each input Newick string (for a small speedup)
      -n, --nosave          don't save the output to a file (must be used with --print)
      -p, --print           print the output to the screen
      -b, --binary BINARY   save the weights array to a binary file. This file can be used to find additional trees. Traditionally this file has the
                            extension .p
    ```

## How to use

Run the commands `mtrip`, `mtrip-suboptimal`, `mtrip-combine` without any arguments to get information on how to use them. The first one is for finding the median tree(s), the second one is for finding the suboptimal trees, and the last one is for combining weights.

## Testing

The package includes a comprehensive test suite to verify correct functionality of all components.

### Running Tests

To run the full test suite:

```bash
# Run all tests
$ python tests/run_tests.py

# Run a specific test file
$ python -m unittest tests/test_newick_parsing.py
```

See the `tests/README.md` file for more details on running and creating tests.

### Example Usage

#### Finding Median Triplet Trees

```bash
# Process input file of Newick strings and write results to default output file
$ mtrip examples/example_5tips.nwk
Using 8 threads.
14/14 complete (100.00)
Input parameters:
Newick file: examples/example_5tips.nwk
Output file: out_example_5tips.nwk
Max threads: 8

Parsing input text file.
* Stripping Newick strings.
* Checking for matching parentheses and semicolon in each GT.

Finding median tree. This might take a while!
* Parsing Newick strings and recording bipartitions in GTs.
* Finding all unique names.
* Calculating each GT bipartition's weight.
* Matching bipartitions to subsets.
* Forming arrays for computations.
* Finding each possible bipartition's weight:
Starting parallel comptuation with a max of 8 threads.
* Finding maximal possible weight of each bipartition.
Best possible triplet count is 26, out of a maximum of 50.

Done!
* Wrote all median triplet trees to out_example_5tips.nwk.
🤖💬 Beep boop, finished in 0.00 seconds.
```

#### Finding Suboptimal Trees

First, run `mtrip` with the `-b` flag to save the weights:

```bash
# Save weights to a binary file for later use with mtrip-suboptimal
$ mtrip examples/example_5tips.nwk -b example_5tips_weights.p
```

Then use `mtrip-suboptimal` to find trees that are close to optimal:

```bash
$ mtrip-suboptimal -y example_5tips_weights.p
Input parameters:
Input file  : example_5tips_weights.p
Output file : outputting to stdout instead
Use stdout  : True
Min fraction: 0.99
Max n trees : 100
Burnin count: 400
RNG seed    : 0

Processing pickle
* Loading pickle
* Verifying
File was created using version 0.26.5 of the utility.
Data for 5 species and maximum triplet score 26.
* Setting minimum viable tree score to 25 (max of -m and -f flags)

Finding trees
* Finding initial splits
* Beginning burn-in
* Could only find 3 trees satisfying the constraint (100 requested)
* Refining all splits
* Sorting by score

Done!
Found 3 trees satisfying the given constraints. 🪆
* Translating to Newick format
* Writing output to stdout.

#26
((A,B),((C,D),E));
#26
((A,B),(C,(D,E)));
#25
((A,B),(D,(C,E)));
```

The output shows three trees with their scores (#26 means the tree satisfies 26 out of 50 possible triplets).

## Developer Documentation

For information on contributing to the project, CI/CD setup, and release process, see [README.dev.md](README.dev.md).

