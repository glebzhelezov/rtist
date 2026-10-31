# mtrip

## How to use

Run the commands `mtrip`, `mtrip-suboptimal`, `mtrip-combine` without any arguments to get information on how to use them. The first one is for finding the median tree(s), the second one is for finding the suboptimal trees, and the last one is for combining weights!

## Building from source

You need a C compiler and CMake 3.15 or newer. The build fetches its Python
build dependencies (Cython, cysignals, scikit-build-core) by itself.

OpenMP is optional but makes the main computation parallel. On Linux, GCC
supports it out of the box. On macOS, install `libomp` with Homebrew
(`brew install libomp`); the build finds it automatically. Without OpenMP the
build still succeeds and runs single-threaded.

```bash
$ git clone https://github.com/glebzhelezov/rtist.git
$ cd rtist
$ uv venv && uv pip install .     # or, in any virtualenv: pip install .
```

Now `mtrip`, `mtrip-suboptimal` and `mtrip-combine` are available whenever
that environment is active, e.g.

```bash
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

### Build options

Pass CMake options through the build frontend with `-C`:

- `-Ccmake.define.MTRIP_NATIVE=ON` tunes the code for the CPU you're building
  on. Faster, but the result only runs on CPUs like yours.
- `-Ccmake.define.MTRIP_OPENMP=OFF` builds without OpenMP even if it's
  available.

For example: `uv pip install . -Ccmake.define.MTRIP_NATIVE=ON`.
