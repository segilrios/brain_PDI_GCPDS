from pathlib import Path

import pytest

from semillero_kb.corpus_manifests import load_candidate_manifest, prepare_bundle_candidates, write_candidate_manifest


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


def test_bundle_preparation_is_capped_deterministic_and_preserves_provenance(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "research/sources").mkdir(parents=True)
    for path in ("research/corpus/seed-manifest.yaml", "research/knowledge/nodes.jsonl", "research/knowledge/edges.jsonl"):
        target = bundle / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("[]\n", encoding="utf-8")
    records = [
        {"id": "b", "kind": "repository", "title": "B", "url": "https://example.test/b", "license": "MIT", "version": 1, "canonical_source": "official", "reference_version": "v1"},
        {"id": "a", "kind": "dataset", "title": "A", "url": "https://example.test/a", "license": "CC0", "version": 1, "canonical_source": "official", "reference_version": "2026"},
    ]
    catalog = bundle / "research/sources/source_catalog.jsonl"
    catalog.write_text("\n".join(__import__("json").dumps(record) for record in records), encoding="utf-8")
    files = ["research/sources/source_catalog.jsonl", "research/corpus/seed-manifest.yaml", "research/knowledge/nodes.jsonl", "research/knowledge/edges.jsonl"]
    (bundle / "MANIFEST.json").write_text(__import__("json").dumps({"generated": "2026-08-30", "files": [{"path": path, "sha256": path} for path in files]}), encoding="utf-8")
    report = prepare_bundle_candidates(bundle, tmp_path / "candidates.yaml", tmp_path / "report.yaml", cap=1)
    assert report["candidate_ids"] == ["dataset:a"]
    assert report["inventory_checksums"]["research/sources/source_catalog.jsonl"] == "research/sources/source_catalog.jsonl"
    assert load_candidate_manifest(tmp_path / "candidates.yaml")[0].provenance.endswith("#a")
    assert report["decision"] == "candidate_only_fail_closed" and "claims" not in (tmp_path / "report.yaml").read_text()


def test_bundle_preparation_rejects_missing_required_metadata(tmp_path):
    bundle = tmp_path / "bundle"
    (bundle / "research/sources").mkdir(parents=True)
    files = ["research/sources/source_catalog.jsonl", "research/corpus/seed-manifest.yaml", "research/knowledge/nodes.jsonl", "research/knowledge/edges.jsonl"]
    for path in files[1:]:
        target = bundle / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("[]\n", encoding="utf-8")
    (bundle / files[0]).write_text('{"id":"paper","kind":"paper","title":"P","url":"https://example.test"}\n', encoding="utf-8")
    (bundle / "MANIFEST.json").write_text(__import__("json").dumps({"generated": "2026-08-30", "files": [{"path": path, "sha256": path} for path in files]}), encoding="utf-8")
    report = prepare_bundle_candidates(bundle, tmp_path / "candidates.yaml", tmp_path / "report.yaml")
    assert report["candidate_ids"] == []
    assert "license" in report["rejections"][0]["reason"]
