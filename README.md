# mtrip

mtrip finds exact median triplet trees. You give it a set of rooted gene trees,
and it finds every species tree that shares as many rooted triplets with them
as possible. The paper below calls the method RTIST; the package and its
commands are called `mtrip`.

> Gleb Zhelezov and James H. Degnan. [*Trying out a million genes to find the
> perfect pair with RTIST*](https://academic.oup.com/bioinformatics/article/38/14/3565/6596045).
> Bioinformatics 38(14):3565-3573, 2022.

## Installation

```bash
pip install mtrip
```

or run it without installing, using [uv](https://docs.astral.sh/uv/):

```bash
uvx mtrip genes.nwk
```

pip installs a prebuilt wheel on Linux (x86_64 and arm64, Alpine included) and
on macOS 11 or newer (Intel and Apple Silicon), for Python 3.10 and up. The
wheels come with OpenMP built in, so mtrip uses all your CPU cores and you
don't need to install anything else. On Windows, use
[WSL](https://learn.microsoft.com/windows/wsl/). Anywhere else, pip compiles
mtrip from source (see [Building from source](#building-from-source)).

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

Each of these trees shares 26 triplets with the gene trees, and no tree shares
more, so both are median triplet trees. When several trees tie for the best
score, mtrip reports all of them.

## Commands

### `mtrip`: median triplet trees

```bash
mtrip genes.nwk                 # writes the trees to out_genes.nwk
mtrip genes.nwk trees.nwk       # ...or to a file you name
mtrip genes.nwk -n -p           # print the trees instead of saving them
mtrip genes.nwk -b weights.p    # also save the weights, for the commands below
```

The input file has one Newick string per line. mtrip ignores branch lengths
and internal node labels, and skips blank lines and lines starting with `#`.
By default it uses all CPUs; `-t N` limits it to N threads.

### `mtrip-suboptimal`: near-optimal trees

This samples trees whose score is close to the best one, using a weights file
saved with `mtrip -b`:

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

The trees come out highest score first, each with its score on the line
above. Set the cutoff with `-f`, as a fraction of the best score (default
0.99), or with `-m`, as an absolute score. `-n` caps the number of trees
(default 100), and `-s` seeds the random sampling.

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

All three commands take `-h` (the full list of options), `-v` (version) and
`-q` (quiet).

## Output and scripting

The commands write only their results to standard output: the trees from
`-p`, and the scored trees from `mtrip-suboptimal`. Progress and other messages
go to standard error, so you can redirect or pipe the results:

```bash
mtrip genes.nwk -n -p > median_trees.nwk
mtrip genes.nwk -n -p -q | some_other_tool    # -q: no progress messages
```

Messages are in color on a terminal, unless the `NO_COLOR` environment
variable is set. The exit code is `0` on success, `1` on an error such as
unreadable input or a malformed Newick string, and `2` on invalid command-line
arguments.

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
  on. It runs faster, but only on CPUs like yours.
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

On every push, GitHub Actions runs the lint checks and the tests on Linux and
macOS (x86_64 and arm64), and builds and tests the wheels. The `Publish`
workflow uploads releases to PyPI using Trusted Publishing.

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
