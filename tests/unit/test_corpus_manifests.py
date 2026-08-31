from pathlib import Path

import pytest

from semillero_kb.corpus_manifests import load_candidate_manifest, write_candidate_manifest


FIXTURE = Path(__file__).parents[1] / "fixtures" / "candidate_manifest.yaml"


def test_candidate_manifest_round_trips_deterministically(tmp_path):
    records = load_candidate_manifest(FIXTURE)
    assert [record.id for record in records] == [
        "dataset:synthetic-water", "repository:synthetic-code", "source:synthetic-candidate",
    ]
    assert {record.admission_state for record in records} == {"candidate"}
    assert (records[0].local_path, records[0].checksum) == ("assets/synthetic-water.csv", "sha256:synthetic-water")
    output = tmp_path / "manifest.yaml"
    write_candidate_manifest(output, records)
    assert load_candidate_manifest(output) == records


@pytest.mark.parametrize("field", ["license", "availability_status", "reference_version"])
def test_candidate_manifest_requires_external_reference_metadata(tmp_path, field):
    text = FIXTURE.read_text(encoding="utf-8").replace(f"    {field}: " + (
        "CC-BY-4.0" if field == "license" else "external_only" if field == "availability_status" else "v1"
    ) + "\n", "", 1)
    path = tmp_path / "invalid.yaml"
    path.write_text(text, encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        load_candidate_manifest(path)


@pytest.mark.parametrize("field", ["id", "version"])
def test_candidate_manifest_requires_identity_and_version(tmp_path, field):
    path = tmp_path / "invalid.yaml"
    target = "  - id: " if field == "id" else f"    {field}: "
    path.write_text(FIXTURE.read_text(encoding="utf-8").replace(target, target.replace(field, f"removed_{field}"), 1), encoding="utf-8")
    with pytest.raises(ValueError, match=field):
        load_candidate_manifest(path)
