"""Helpers shared by the mtrip command-line tools."""

import argparse
import pickle
import sys
import textwrap

import mtrip

# ANSI text styles.
BOLD = "\033[1m"
UNDERLINE = "\033[4m"
ITALICS = "\033[3m"
END = "\033[0m"

# A weights file ("pickle") is a pickled dict with these keys. MAGIC_KEY ->
# MAGIC_VALUE guards against loading an unrelated pickle by mistake; it is
# not a security measure.
MAGIC_KEY = "abigsecret"
MAGIC_VALUE = "ogurets"
WEIGHTS_KEYS = (
    "version",
    "nwks",
    "median_nwks",
    "reverse_dictionary",
    "triplet_weights",
    "stack",
    "best_biparts",
)
PICKLE_PROTOCOL = 4


class FriendlyParser(argparse.ArgumentParser):
    """Print the full help text, not just the usage line, on a usage error.

    Trick by Steven Berthard:
    https://groups.google.com/g/argparse-users/c/LazV_tEQvQw
    """

    def error(self, message):
        sys.stderr.write(f"error: {message}\n")
        self.print_help()
        sys.exit(2)


def add_version_argument(parser):
    parser.add_argument("-v", "--version", action="version", version=mtrip.__version__)


class WeightsFileError(Exception):
    """A weights file can't be read or isn't a weights file."""


def save_weights(path, **fields):
    """Write a weights file. fields must be exactly WEIGHTS_KEYS."""
    if set(fields) != set(WEIGHTS_KEYS):
        raise ValueError(f"expected fields {WEIGHTS_KEYS}, got {tuple(fields)}")
    data = {MAGIC_KEY: MAGIC_VALUE, **{k: fields[k] for k in WEIGHTS_KEYS}}
    with open(path, "wb") as f:
        pickle.dump(data, f, protocol=PICKLE_PROTOCOL)


def load_weights(path):
    """Read and sanity-check a weights file; raise WeightsFileError if bad."""
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)
    except OSError as e:
        raise WeightsFileError(f"Can't open input file {path} for reading.") from e
    except (pickle.UnpicklingError, EOFError) as e:
        raise WeightsFileError(f"{e}\nCan't unpickle (wrong file?).") from e

    if not (isinstance(data, dict) and data.get(MAGIC_KEY) == MAGIC_VALUE):
        raise WeightsFileError("This does not seem to be a valid file.")
    missing = [k for k in WEIGHTS_KEYS if k not in data]
    if missing:
        raise WeightsFileError(f"Weights file is missing {', '.join(missing)}.")
    return data


def pickle_warning(filename):
    """Ask before unpickling filename; exit if the user declines."""
    print(BOLD + "From the Python 3 manual:" + END)
    s = (
        "Only unpickle data you trust. It is possible to construct "
        "malicious pickle data which will execute arbitrary code during "
        "unpickling. Never unpickle data that could have come from an "
        "untrusted source, or that could have been tampered with."
    )
    print(textwrap.fill(s))
    print()
    s = "You can avoid this interactive warning in the future by using the -y flag."
    print(textwrap.fill(s))
    print()

    verification = ""

    while verification not in {"y", "n"}:
        verification = input(f"Load the file {BOLD}{filename}{END}? (y/n) ")
        verification = verification.lower().strip()

    if verification == "n":
        print("Aborting.")
        sys.exit(0)
