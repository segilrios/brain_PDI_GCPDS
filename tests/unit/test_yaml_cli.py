from pathlib import Path

import pytest

from semillero_kb.cli import main
from semillero_kb.yaml_records import dump_yaml, load_yaml


FIXTURE = Path(__file__).parents[1] / "fixtures" / "valid_claim.yaml"


def test_yaml_round_trip_is_deterministic_and_preserves_identity():
    record = load_yaml(FIXTURE)
    assert (record.id, record.version) == ("claim:synthetic-water", 3)
    assert dump_yaml(record) == dump_yaml(load_yaml(FIXTURE))


def test_yaml_validation_is_typed_and_clear(tmp_path):
    invalid = tmp_path / "invalid.yaml"
    invalid.write_text("id: claim:bad\nversion: 1\n")
    with pytest.raises(ValueError, match="invalid Claim record"):
        load_yaml(invalid)


def test_cli_validate_reports_success(capsys):
    assert main(["validate", str(FIXTURE)]) == 0
    assert "valid Claim id=claim:synthetic-water version=3" in capsys.readouterr().out


def test_cli_validate_reports_failure(tmp_path, capsys):
    invalid = tmp_path / "unknown.yaml"
    invalid.write_text("id: unknown:record\n")
    with pytest.raises(SystemExit) as error:
        main(["validate", str(invalid)])
    assert error.value.code == 2
    assert "unknown record type prefix" in capsys.readouterr().err


def test_canonical_layout_is_present():
    root = Path(__file__).parents[2] / "research"
    assert {"sources", "claims", "graph", "experiments", "corpus", "assets", "taxonomy"} == {
        path.name for path in root.iterdir() if path.is_dir()
    }