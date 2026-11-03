# CLAUDE.md

Guidance for Claude Code (claude.ai/code) when working in this repository.

## Project

`mtrip` finds exact median triplet trees: every rooted species tree that shares
the most triplets with a set of gene trees. It implements RTIST (Zhelezov &
Degnan, Bioinformatics 2022). The repo is `rtist`, the PyPI package and the
commands are `mtrip`. License: GPL-3.0-only.

Hybrid C / Cython / Python, built with CMake through scikit-build-core, and
developed with uv. Supported: Linux (glibc and musl) and macOS, x86_64 and
arm64, Python 3.10+. No Windows.

## Commands

```bash
uv sync                                     # dev env in .venv (editable install + dev tools)
uv run pytest                               # all tests
uv run pytest tests/test_cli.py -k quiet    # a subset
uv run mtrip examples/example_5tips.nwk -n -p
uv run ruff format && uv run ruff check     # Python
uv run clang-format -i lib/*.c lib/*.h      # C (LLVM style, 4 spaces; see .clang-format)
uv build                                    # sdist + wheel into dist/
```

`uv run` rebuilds the compiled modules automatically when a C, header, `.pyx`
or CMake file changes (`[tool.uv] cache-keys` in pyproject.toml). Build options:
`-Ccmake.define.MTRIP_OPENMP=OFF` (serial build) and
`-Ccmake.define.MTRIP_NATIVE=ON` (host-tuned, non-portable); in CI the serial
build uses `SKBUILD_CMAKE_DEFINE=MTRIP_OPENMP=OFF`. On macOS, OpenMP comes from
Homebrew's `libomp`, found automatically.

ruff and clang-format are pinned to exact versions in the `dev` dependency
group, and CI checks formatting with those versions; run them through `uv run`
so your output matches CI.

## Layout

- `lib/`: C core, built as the static library `ctriplet` (`lib/CMakeLists.txt`,
  buildable on its own). `weights_omp.c` has the OpenMP-parallel
  `fill_compressed_weight_representation`; `lookup_table.c` has the base-2 to
  base-3 ("two2three") index table. Every OpenMP call is guarded by
  `#ifdef _OPENMP` so the code also builds serially.
- `CMakeLists.txt`: transpiles and builds the three Cython extensions
  (`mtrip.triplet_omp` from `triplet_omp_py.pyx`, `mtrip.bitsnbobs`,
  `mtrip.scipycomb` from `scipy_comb.pyx`) with cython-cmake, and links
  `triplet_omp` against `ctriplet`.
- `src/mtrip/median_tree_reconstruction.py`: the algorithm, in Python.
- `src/mtrip/cli/`: the three commands, `find.py` (`mtrip`), `suboptimal.py`
  (`mtrip-suboptimal`), `combine.py` (`mtrip-combine`), with shared code in
  `_common.py` (argument parsing, logging setup, colors, weights-file I/O).
- `tests/`: pytest. `brute.py` has independent brute-force reference
  implementations; `common.py` has shared helpers (import it, there is no
  conftest). Examples in `examples/` double as test inputs.
- `.github/workflows/`: `ci.yml` (lint + tests on 4 platforms + a no-OpenMP
  build), `wheels.yml` (cibuildwheel; config in `[tool.cibuildwheel]`),
  `publish.yml` (manual; uploads to PyPI/TestPyPI via Trusted Publishing after
  CI and wheels pass).

## Algorithm pipeline

1. **Parse** (`simplify_nwk`, `get_names`): strip branch lengths and internal
   labels; map each taxon to a bit, so a set of taxa is an int bitmask.
2. **Bipartitions** (`get_biparts`, `splitter`): each internal node of a gene
   tree is a split `(a, b)` of disjoint bitmasks. `get_weights` (or
   `get_weights_parallel`, multiprocessing) counts them over all gene trees;
   `get_subset_biparts` groups them by `a | b`.
3. **Weight expansion** (C): `py_compressed_weight_rep` calls
   `fill_compressed_weight_representation`, which computes, for every possible
   bipartition of every subset, the number of gene-tree triplets it agrees
   with. The array is indexed by a base-3 encoding of `(a, b)` (each taxon is
   in a, in b, or neither), so it has about 2·3^(n−1) entries.
4. **Subset DP** (`get_stack`): over subsets in order of size (Gosper's hack,
   `get_binary_subsets`), the best score of each subset is the best over its
   splits of weight + best(a) + best(b). Every optimal split is kept.
5. **Reconstruction** (`get_all_trees`): walk the kept splits from the full set
   down to leaves to enumerate *all* optimal trees.

`process_nwks` does steps 1–3; `median_triplet_trees` runs everything.
`mtrip-suboptimal` reuses the saved weights (step 3 output) to sample trees
whose score is within a fraction of the best.

## Conventions

- **stdout is for results only** (trees from `-p`, `mtrip-suboptimal`'s
  output). Everything else goes through `logging` (loggers under `mtrip`;
  the commands use `mtrip.cli`) to stderr. Library code never prints.
- Commands exit 0 on success, 1 on runtime errors, 2 on usage errors (use
  `parser.error`).
- Color only when stderr is a terminal and `NO_COLOR` is unset (`style()` in
  `_common.py`).
- Weights files are pickles with a fixed layout (`save_weights`/`load_weights`);
  keep it backward compatible so old `.p` files still load.
- Results must not depend on the thread count or on whether OpenMP is used; the
  tests check this against brute force.
- The version lives only in `pyproject.toml`; `mtrip.__version__` reads it from
  the installed metadata.
- cysignals' `sig_on()` is compiled into `triplet_omp`, and its ABI changed in
  1.12.6, so the module only works with cysignals from the side it was built
  against. The cysignals requirements in `[build-system]` and `dependencies`
  must stay identical (split at Python 3.13; see the comment in
  pyproject.toml). The wheel tests install dependencies from wheels only, so a
  pin without wheels for some platform fails there.

## Known limitations

- 20 or more taxa overflow the 32-bit indices in C (2·3^19 > INT_MAX).
