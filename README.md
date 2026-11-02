# mtrip

Find **exact median triplet trees**: given a set of rooted gene trees, find
every species tree that shares the largest possible number of rooted triplets
with them. This is the method called RTIST in the paper below. The package and
its commands are called `mtrip`.

> Gleb Zhelezov and James H. Degnan. [*Trying out a million genes to find the
> perfect pair with RTIST*](https://academic.oup.com/bioinformatics/article/38/14/3565/6596045).
> Bioinformatics 38(14):3565–3573, 2022.

## Installation

```bash
pip install mtrip
```

or run it without installing, using [uv](https://docs.astral.sh/uv/):

```bash
uvx mtrip genes.nwk
```

Prebuilt wheels are available for Linux (x86_64 and arm64, including Alpine)
and macOS 11+ (Intel and Apple Silicon), for Python 3.10 and newer. They
include OpenMP, so the main computation runs on all CPU cores with nothing
else to install. On Windows, use [WSL](https://learn.microsoft.com/windows/wsl/).
On other systems pip builds from source; see
[Building from source](#building-from-source).

## Quick start

`genes.nwk` has one rooted gene tree per line, in Newick format:

```
((A,B),(C,(D,E)));
(((A,C),B),(D,E));
(((A,D),B),(C,E));
((A,E),((B,C),D));
(A,(B,((C,D),E)));
```

```console
$ mtrip genes.nwk -n -p
...
Best possible triplet count is 26, out of a maximum of 50.
...
((A,B),((C,D),E));
((A,B),(C,(D,E)));
```

Both trees are median triplet trees: each shares 26 triplets with the gene
trees, and no tree shares more. `mtrip` always reports *all* optimal trees.

## Commands

### `mtrip`: median triplet trees

```bash
mtrip genes.nwk                 # writes the trees to out_genes.nwk
mtrip genes.nwk trees.nwk       # ...or to a file you name
mtrip genes.nwk -n -p           # print the trees instead of saving them
mtrip genes.nwk -b weights.p    # also save the weights, for the commands below
```

Input: one Newick string per line. Branch lengths and internal node labels are
ignored, and blank lines and lines starting with `#` are skipped. Use
`-t N` to limit the number of threads (default: all CPUs).

### `mtrip-suboptimal`: near-optimal trees

From a weights file saved with `mtrip -b`, sample trees whose score is close
to the best one:

```console
$ mtrip-suboptimal weights.p -f 0.9 -n 5
#26
((A,B),((C,D),E));
#25
((A,B),(D,(C,E)));
#24
(A,(B,(C,(D,E))));
...
```

Each tree is preceded by its score, highest first. `-f` sets the minimum score
as a fraction of the best (default 0.99), or `-m` as an absolute number; `-n`
caps the number of trees (default 100), and `-s` seeds the random sampling.

### `mtrip-combine`: combine runs

Weights from separate runs (for example, on parts of a large data set) add up.
Combine them, then work with the result as if it came from one run:

```bash
mtrip part1.nwk -b part1.p
mtrip part2.nwk -b part2.p
mtrip-combine part1.p part2.p -o all.p
mtrip-suboptimal all.p -f 1         # the median trees of the combined data
```

All inputs must have the same taxa.

> [!NOTE]
> Weights files are Python pickles, and loading a pickle can run arbitrary
> code. Only load weights files you created or trust. `mtrip-suboptimal` asks
> before loading one; `-y` skips the question.

Every command takes `-h` for the full list of options, `-v` for its version,
and `-q` for quiet mode.

## Output and scripting

- **Only results go to standard output**: the trees from `-p`, and
  `mtrip-suboptimal`'s scored trees. Progress and messages go to standard
  error, so redirecting and piping work:

  ```bash
  mtrip genes.nwk -n -p > median_trees.nwk
  mtrip genes.nwk -n -p -q | some_other_tool    # -q: no progress messages
  ```

- Messages are colored only on a terminal, and never when the `NO_COLOR`
  environment variable is set.
- Exit codes: `0` on success, `1` on errors (unreadable input, a malformed
  Newick string, ...), `2` on invalid command-line arguments.

## Limits

The search is exact, so its cost grows exponentially with the number of taxa
*n* (it stores about 2·3<sup>n−1</sup> weights): about 1 GB of memory at 18
taxa and about 3 GB at 19. The number of gene trees matters much less. Inputs
with 20 or more taxa are not supported yet.

## Building from source

You need a C compiler and CMake 3.15 or newer. The build fetches its Python
build dependencies (Cython, cysignals, scikit-build-core) itself.

OpenMP is optional but makes the main computation parallel. On Linux, GCC
supports it out of the box. On macOS, install `libomp` with Homebrew
(`brew install libomp`); the build finds it automatically. Without OpenMP the
build still succeeds and runs single-threaded.

```bash
git clone https://github.com/glebzhelezov/rtist.git
cd rtist
pip install .
```

Build options, passed through pip (or `uv pip`) with `-C`:

- `-Ccmake.define.MTRIP_NATIVE=ON` tunes the code for the CPU you're building
  on. Faster, but the result only runs on CPUs like yours.
- `-Ccmake.define.MTRIP_OPENMP=OFF` builds without OpenMP even if it's
  available.

## Development

The project uses [uv](https://docs.astral.sh/uv/):

```bash
uv sync                                    # .venv with mtrip (editable) and dev tools
uv run pytest                              # test suite
uv run mtrip examples/example_5tips.nwk -n -p
uv run ruff format && uv run ruff check    # Python formatting and lint
uv run clang-format -i lib/*.c lib/*.h     # C formatting
```

Edits to `.py` files take effect immediately. When a C, `.pyx` or CMake file
changes, the next `uv run` rebuilds the compiled modules.

GitHub Actions runs the lint checks and tests on Linux and macOS (x86_64 and
arm64) for every push, and builds and tests the wheels. Releases are uploaded
to PyPI by the `Publish` workflow through Trusted Publishing.

## Citation

```bibtex
@article{zhelezov2022trying,
  title={Trying out a million genes to find the perfect pair with {RTIST}},
  author={Zhelezov, Gleb and Degnan, James H},
  journal={Bioinformatics},
  volume={38},
  number={14},
  pages={3565--3573},
  year={2022},
  publisher={Oxford University Press}
}
```

## License

GPL-3.0. See [LICENSE](https://github.com/glebzhelezov/rtist/blob/HEAD/LICENSE).
