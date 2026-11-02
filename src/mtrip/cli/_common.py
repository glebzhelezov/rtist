"""Helpers shared by the mtrip command-line tools.

Output conventions: results (trees) go to stdout; everything else (progress,
status, warnings, errors, prompts) goes to stderr, so that stdout can be piped
or redirected. Progress messages are logged through the "mtrip" logger and are
silenced by --quiet; warnings and errors are not.
"""

import argparse
import logging
import os
import pickle
import sys
import textwrap

import mtrip

# ANSI text styles; apply them with style(), which drops them when stderr
# isn't a terminal or NO_COLOR is set.
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


def add_common_arguments(parser):
    """--version and --quiet, shared by every command."""
    parser.add_argument("-v", "--version", action="version", version=mtrip.__version__)
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="only print warnings and errors (to stderr), besides the results",
    )


def setup_logging(quiet=False):
    """Send mtrip's log messages to stderr as plain lines."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("mtrip")
    logger.handlers[:] = [handler]
    logger.setLevel(logging.WARNING if quiet else logging.INFO)
    logger.propagate = False


def use_color():
    """Whether to style stderr output (https://no-color.org)."""
    return sys.stderr.isatty() and not os.environ.get("NO_COLOR")


def style(text, *codes):
    """Wrap text in ANSI codes if use_color(), else return it unchanged."""
    if not codes or not use_color():
        return text
    return "".join(codes) + text + END


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
    """Ask (on stderr) before unpickling filename; exit if the user declines.

    Reads the answer from stdin; end of input counts as "no".
    """

    def say(text=""):
        print(text, file=sys.stderr)

    say(style("From the Python 3 manual:", BOLD))
    s = (
        "Only unpickle data you trust. It is possible to construct "
        "malicious pickle data which will execute arbitrary code during "
        "unpickling. Never unpickle data that could have come from an "
        "untrusted source, or that could have been tampered with."
    )
    say(textwrap.fill(s))
    say()
    s = "You can avoid this interactive warning in the future by using the -y flag."
    say(textwrap.fill(s))
    say()

    verification = ""

    while verification not in {"y", "n"}:
        print(
            f"Load the file {style(str(filename), BOLD)}? (y/n) ",
            end="",
            file=sys.stderr,
            flush=True,
        )
        line = sys.stdin.readline()
        if not line:  # end of input
            say()
            verification = "n"
            break
        verification = line.lower().strip()

    if verification == "n":
        say("Aborting.")
        sys.exit(0)
