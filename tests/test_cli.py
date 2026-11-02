"""Smoke tests for the three commands, run as subprocesses."""

import subprocess
import sys

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
    assert nosave.returncode == 1  # --nosave without --print
    missing = run("find", tmp_path / "does_not_exist.nwk", cwd=tmp_path)
    assert missing.returncode == 1


def test_find_rejects_line_without_semicolon(tmp_path):
    bad = tmp_path / "bad.nwk"
    bad.write_text("((A,B),C);\n((A,C),B)\n")
    result = run("find", bad, "-n", "-p", cwd=tmp_path)
    assert result.returncode == 1
    assert "Line 2" in result.stdout + result.stderr


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


def make_weights(tmp_path, name="w.p"):
    weights = tmp_path / name
    result = run(
        "find", EXAMPLES / "example_5tips.nwk", "-n", "-p", "-b", weights, cwd=tmp_path
    )
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
