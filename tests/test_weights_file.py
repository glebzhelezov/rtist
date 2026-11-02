"""The weights ("pickle") file format written by mtrip -b."""

import pickle

import pytest

from mtrip.cli._common import WeightsFileError, load_weights, save_weights

FIELDS = {
    "version": "0.26.5",
    "nwks": ["((A,B),C);"],
    "median_nwks": ["((A,B),C);"],
    "reverse_dictionary": ["A", "B", "C"],
    "triplet_weights": [0, 1, 2],
    "stack": [0, 0, 0, 0, 0, 0, 0, 1],
    "best_biparts": [[]] * 8,
}


def test_round_trip(tmp_path):
    path = tmp_path / "w.p"
    save_weights(path, **FIELDS)
    data = load_weights(path)
    assert {k: data[k] for k in FIELDS} == FIELDS


def test_reads_files_written_by_older_versions(tmp_path):
    # Exactly what mtrip's find command wrote before the shared helpers.
    labels = ["abigsecret", *FIELDS]
    values = ["ogurets", *FIELDS.values()]
    path = tmp_path / "old.p"
    with open(path, "wb") as f:
        pickle.dump(dict(zip(labels, values, strict=True)), f, protocol=4)
    assert load_weights(path)["reverse_dictionary"] == ["A", "B", "C"]


def test_save_requires_exactly_the_known_fields(tmp_path):
    with pytest.raises(ValueError):
        save_weights(tmp_path / "w.p", **{**FIELDS, "extra": 1})
    with pytest.raises(ValueError):
        save_weights(tmp_path / "w.p", version="x")


@pytest.mark.parametrize(
    "content",
    [
        b"",  # empty file
        b"not a pickle",
        pickle.dumps({"some": "dict"}),  # a pickle, but not a weights file
        pickle.dumps(["a", "list"]),
        pickle.dumps({"abigsecret": "ogurets"}),  # magic but no fields
    ],
)
def test_rejects_non_weights_files(tmp_path, content):
    path = tmp_path / "bad.p"
    path.write_bytes(content)
    with pytest.raises(WeightsFileError):
        load_weights(path)


def test_missing_file(tmp_path):
    with pytest.raises(WeightsFileError, match="Can't open"):
        load_weights(tmp_path / "nope.p")
