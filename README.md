# mtrip

MTrip has a few dependencies.

Python:
- Cython
- Cysignals
- Pyinstaller (if you want binaries)

C:
- GCC with OpenMP support

## How to use

Run the commands `mtrip`, `mtrip-suboptimal`, `mtrip-combine` without any arguments to get information on how to use them. The first one is for finding the median tree(s), the second one is for finding the suboptimal trees, and the last one is for combining weights!

## Installation instructions for Linux

1. Install [conda](https://docs.conda.io/en/latest/miniconda.html)
2. Clone this repository and change into the directory:
```bash
$ git clone https://github.com/glebzhelezov/mtrip.git
$ cd mtrip
```

3. Create a conda environment for mtrip:

```bash
$ conda env create -f mtrip.yaml
```

4. Activate it:

```bash
$ conda activate mtrip
```

5. Make it:

```bash
$ make
```

Now you can use mtrip any time the conda environment is activated, e.g.

```bash
$ conda activate mtrip
$ mtrip
error: the following arguments are required: i
usage: mtrip [-h] [-v] [-t THREADS] [--novalidate] [-n] [-p] [-b BINARY] i [o]
....
$ mtrip-suboptimal
error: the following arguments are required: i
usage: mtrip-suboptimal [-h] [-p] [-m MINSCORE] [-f FRACTION] [-n NTREES]
                        [-b BURNIN] [-s SEED] [-y] [-v]
                        i [o]
...
$ mtrip-combine
This utility is for combining weight pickles produced by mtrip.
Usage:	$ mtrip-combine in_pickle_1.p ... in_pickle_n.p
....
```

## Installation instructions for OS X

In OS X, "gcc" is symlinked to Clang, which does not have support for OpenMP. So please install GCC with OpenMP support using Homebrew, and then use the instructions above. You could likely do the same thing with Clang with OpenMP support enabled, but I've not tried it! 

## Creating binaries

It is possible to make binaries to stick in your path. For this, you need pyinstaller:

```bash
$ conda activate mtrip
$ conda install -y pyinstaller
```

Then, from the same directory as above:

```bash
$ make binary
```

After some time you will have three binaries in the directory `dist`, which you can use however you wish. You can put them in `~/.local/bin` or `/usr/local/bin` to have the three programs available as commands, or put them in whatever directory you want to use.