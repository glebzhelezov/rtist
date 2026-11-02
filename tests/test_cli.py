"""Smoke tests for the three commands, run as subprocesses."""

import os
import subprocess
import sys

import pytest
from common import EXAMPLES


def run(module, *args, cwd):
    return subprocess.run(
        [sys.executable, "-m", f"mtrip.cli.{module}", *map(str, args)],
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=120,
    )


def tree_lines(text):
    return sorted(line for line in text.splitlines() if line.endswith(";"))


def test_version(tmp_path):
    from mtrip import __version__

    for module in ("find", "suboptimal", "combine"):
        result = run(module, "--version", cwd=tmp_path)
        assert result.returncode == 0
        assert result.stdout.strip() == __version__


@pytest.mark.skipif(
    "MTRIP_EXPECT_OPENMP" not in os.environ,
    reason="set MTRIP_EXPECT_OPENMP=1 (or 0) to check how mtrip was built",
)
def test_openmp_build(tmp_path):
    """CI sets MTRIP_EXPECT_OPENMP, so a build that silently lost OpenMP fails."""
    result = run(
        "find", EXAMPLES / "example_5tips.nwk", "-n", "-p", "-t", 2, cwd=tmp_path
    )
    assert result.returncode == 0, result.stderr
    parallel = "Using 2 threads." in result.stderr
    assert parallel == (os.environ["MTRIP_EXPECT_OPENMP"] == "1"), result.stderr


def test_find_writes_output_file(tmp_path):
    result = run("find", EXAMPLES / "example_5tips.nwk", "-t", 2, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    out = (tmp_path / "out_example_5tips.nwk").read_text()
    assert tree_lines(out) == ["((A,B),((C,D),E));", "((A,B),(C,(D,E)));"]


def test_find_print_without_saving(tmp_path):
    result = run("find", EXAMPLES / "example_5tips.nwk", "-n", "-p", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert tree_lines(result.stdout) == ["((A,B),((C,D),E));", "((A,B),(C,(D,E)));"]
    assert list(tmp_path.iterdir()) == []


def test_find_usage_errors(tmp_path):
    assert run("find", cwd=tmp_path).returncode == 2  # missing input
    nosave = run("find", EXAMPLES / "example.nwk", "-n", cwd=tmp_path)
    assert nosave.returncode == 2  # --nosave without --print
    threads = run("find", EXAMPLES / "example.nwk", "-t", 0, cwd=tmp_path)
    assert threads.returncode == 2
    missing = run("find", tmp_path / "does_not_exist.nwk", cwd=tmp_path)
    assert missing.returncode == 1
    assert "does_not_exist.nwk" in missing.stderr


def test_find_rejects_line_without_semicolon(tmp_path):
    bad = tmp_path / "bad.nwk"
    bad.write_text("((A,B),C);\n\n((A,C),B)\n")
    result = run("find", bad, "-n", "-p", cwd=tmp_path)
    assert result.returncode == 1
    assert "Line 3" in result.stderr
    assert result.stdout == ""


def test_find_skips_blank_lines_and_comments(tmp_path):
    lines = (EXAMPLES / "example_5tips.nwk").read_text().splitlines()
    padded = tmp_path / "padded.nwk"
    padded.write_text("\n# a comment\n" + "\n\n".join(lines) + "\n\n   \n")
    for validate in ([], ["--novalidate"]):
        result = run("find", padded, "-n", "-p", *validate, cwd=tmp_path)
        assert result.returncode == 0, result.stderr
        assert tree_lines(result.stdout) == [
            "((A,B),((C,D),E));",
            "((A,B),(C,(D,E)));",
        ]


def test_find_empty_input(tmp_path):
    empty = tmp_path / "empty.nwk"
    empty.write_text("# nothing here\n\n")
    result = run("find", empty, "-n", "-p", cwd=tmp_path)
    assert result.returncode == 1
    assert "No Newick strings" in result.stderr


def test_stdout_has_only_results(tmp_path):
    """Everything except the trees goes to stderr, without color codes."""
    result = run("find", EXAMPLES / "example_5tips.nwk", "-n", "-p", cwd=tmp_path)
    assert result.returncode == 0
    assert all(line.endswith(";") for line in result.stdout.splitlines())
    assert "Best possible triplet count is 26" in result.stderr
    assert "\x1b[" not in result.stderr  # not a terminal: no ANSI codes

    weights = make_weights(tmp_path)
    result = run("suboptimal", "-y", weights, cwd=tmp_path)
    assert result.returncode == 0
    for line in result.stdout.splitlines():
        assert line.endswith(";") or (line[0] == "#" and line[1:].isdigit())
    assert "Found 3 trees" in result.stderr


def test_quiet(tmp_path):
    result = run("find", EXAMPLES / "example_5tips.nwk", "-n", "-p", "-q", cwd=tmp_path)
    assert result.returncode == 0
    assert result.stderr == ""
    assert len(tree_lines(result.stdout)) == 2

    weights = make_weights(tmp_path)
    result = run("suboptimal", "-y", "-q", weights, cwd=tmp_path)
    assert (result.returncode, result.stderr) == (0, "")
    result = run("combine", "-q", weights, weights, cwd=tmp_path)
    assert (result.returncode, result.stderr) == (0, "")

    # Errors still get through.
    missing = run("find", "-q", tmp_path / "nope.nwk", cwd=tmp_path)
    assert missing.returncode == 1
    assert "nope.nwk" in missing.stderr


def test_suboptimal_usage_errors(tmp_path):
    weights = make_weights(tmp_path)
    for bad in (["-f", "0"], ["-f", "1.5"], ["-n", "0"], ["-m", "-5"], ["-b", "1"]):
        result = run("suboptimal", "-y", weights, *bad, cwd=tmp_path)
        assert result.returncode == 2, bad


def test_suboptimal_prompt(tmp_path):
    weights = make_weights(tmp_path)

    def answer(text):
        return subprocess.run(
            [sys.executable, "-m", "mtrip.cli.suboptimal", str(weights)],
            input=text,
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=120,
        )

    declined = answer("n\n")
    assert declined.returncode == 0
    assert declined.stdout == ""
    assert "Load the file" in declined.stderr and "Aborting." in declined.stderr

    assert answer("").stdout == ""  # end of input counts as "no"

    accepted = answer("maybe\ny\n")
    assert accepted.returncode == 0
    assert "#26" in accepted.stdout.splitlines()


def test_suboptimal_and_combine_from_saved_weights(tmp_path):
    weights = tmp_path / "w.p"
    result = run(
        "find", EXAMPLES / "example_5tips.nwk", "-n", "-p", "-b", weights, cwd=tmp_path
    )
    assert result.returncode == 0, result.stderr

    result = run("suboptimal", "-y", weights, "-f", "0.95", cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    lines = result.stdout.splitlines()
    scored = [(lines[i - 1], lines[i]) for i, s in enumerate(lines) if s.endswith(";")]
    scores = [int(score[1:]) for score, _ in scored]
    assert scores == sorted(scores, reverse=True)
    # The cutoff is int(fraction * best score), rounded down.
    assert min(scores) >= int(0.95 * 26)
    assert {tree for score, tree in scored if score == "#26"} == {
        "((A,B),((C,D),E));",
        "((A,B),(C,(D,E)));",
    }

    result = run("combine", weights, weights, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert (tmp_path / "combined_weights.p").exists()

    # Combining two copies doubles every score; the optimal trees stay the same.
    result = run(
        "suboptimal", "-y", tmp_path / "combined_weights.p", "-f", "1", cwd=tmp_path
    )
    assert result.returncode == 0, result.stderr
    assert "#52" in result.stdout.splitlines()


def test_suboptimal_trees_are_distinct(tmp_path):
    """Sampling 30 of the candidates must not pick any of them twice."""
    weights = make_weights(tmp_path, example="large_example.nwk")
    for seed in range(3):
        result = run(
            "suboptimal",
            "-y",
            "-q",
            "-f",
            "0.9",
            "-n",
            30,
            "-s",
            seed,
            weights,
            cwd=tmp_path,
        )
        assert result.returncode == 0, result.stderr
        trees = tree_lines(result.stdout)
        assert len(trees) == 30
        assert len(set(trees)) == 30


def make_weights(tmp_path, name="w.p", example="example_5tips.nwk"):
    weights = tmp_path / name
    result = run("find", EXAMPLES / example, "-n", "-p", "-b", weights, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    return weights


def test_combine_output_option_and_default_names(tmp_path):
    weights = make_weights(tmp_path)
    assert (
        run("combine", weights, weights, "-o", "both.p", cwd=tmp_path).returncode == 0
    )
    assert (tmp_path / "both.p").exists()
    # Without -o, never overwrite: combined_weights.p, then combined_weights_1.p.
    for expected in ("combined_weights.p", "combined_weights_1.p"):
        assert run("combine", weights, weights, cwd=tmp_path).returncode == 0
        assert (tmp_path / expected).exists()


def test_combine_rejects_bad_inputs(tmp_path):
    weights = make_weights(tmp_path)
    assert run("combine", weights, cwd=tmp_path).returncode == 2  # only one input
    not_weights = tmp_path / "not_weights.p"
    not_weights.write_bytes(b"definitely not a pickle")
    result = run("combine", weights, not_weights, cwd=tmp_path)
    assert result.returncode == 1
    assert "not_weights.p" in result.stdout + result.stderr


def test_installed_console_scripts(tmp_path):
    """The entry points behave like python -m (module name differs: __main__)."""
    from pathlib import Path

    bindir = Path(sys.executable).parent
    result = subprocess.run(
        [bindir / "mtrip", EXAMPLES / "example_5tips.nwk", "-n", "-p"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert result.returncode == 0, result.stderr
    assert len(tree_lines(result.stdout)) == 2
    assert "Input parameters:" in result.stderr
    for name in ("mtrip-suboptimal", "mtrip-combine"):
        assert (bindir / name).exists()
