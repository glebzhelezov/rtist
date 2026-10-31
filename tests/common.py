from pathlib import Path

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


def read_nwks(path):
    """Read gene trees the way the mtrip command does (skipping comments)."""
    with open(path) as f:
        return [s for s in (line.strip() for line in f) if s and s[0] != "#"]
