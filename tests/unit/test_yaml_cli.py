from pathlib import Path

import pytest

from semillero_kb.cli import main
from semillero_kb.models import Lifecycle
from semillero_kb.validation import transition_record
from semillero_kb.yaml_records import dump_yaml, load_yaml


FIXTURE = Path(__file__).parents[1] / "fixtures" / "valid_claim.yaml"
CURATION_FIXTURE = Path(__file__).parents[1] / "fixtures" / "candidate_curation.yaml"


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


def test_yaml_persists_lifecycle_history(tmp_path):
    record = transition_record(load_yaml(FIXTURE), Lifecycle.DEPRECATED, actor="curator",
                               reason="superseded terminology", transition_date="2026-08-30")
    path = tmp_path / "deprecated.yaml"
    path.write_text(dump_yaml(record), encoding="utf-8")
    loaded = load_yaml(path)
    assert loaded.lifecycle_history[-1].actor == "curator"


def test_cli_curate_and_promote_are_fail_closed(tmp_path, capsys):
    candidate = tmp_path / "candidate.yaml"
    candidate.write_text(CURATION_FIXTURE.read_text(encoding="utf-8"), encoding="utf-8")
    seed, verified = tmp_path / "seed.yaml", tmp_path / "verified.yaml"
    assert main(["curate", str(candidate), "--curator", "curator:ada", "--reason", "relevant", "--output", str(seed)]) == 0
    assert main(["promote", str(seed), "--curator", "curator:ada", "--reason", "checked", "--validation-evidence", "evidence:review", "--output", str(verified)]) == 0
    assert load_yaml(verified).admission_state == "verified_expansion"
    with pytest.raises(SystemExit): main(["promote", str(candidate), "--curator", "curator:ada", "--reason", "skip", "--validation-evidence", "evidence:x", "--output", str(seed)])
    assert "only human seeds can be promoted" in capsys.readouterr().err
