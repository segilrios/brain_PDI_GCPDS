"""Canonical candidate manifests for source and external-reference metadata."""
from datetime import date
import json
from pathlib import Path

import yaml
from pydantic import BaseModel

from .models import AdmissionState, DatasetReference, RepositoryReference, Source
from .yaml_records import load_record

ManifestRecord = Source | DatasetReference | RepositoryReference
DEFAULT_BUNDLE_IMPORT_CAP = 20


def _validate_candidate(record: BaseModel) -> ManifestRecord:
    if not isinstance(record, (Source, DatasetReference, RepositoryReference)):
        raise ValueError(f"manifest record {record.id} must be a source, dataset, or repository")
    for field in ("id", "provenance", "version", "license", "availability_status"):
        if not getattr(record, field):
            raise ValueError(f"manifest record requires {field}")
    if isinstance(record, (DatasetReference, RepositoryReference)) and not record.reference_version:
        raise ValueError("external reference manifest requires reference_version")
    if record.admission_state is not AdmissionState.CANDIDATE:
        raise ValueError(f"manifest record {record.id} must have admission_state candidate")
    return record


def _load_candidate(data: object) -> ManifestRecord:
    if not isinstance(data, dict):
        raise ValueError("manifest record must be a mapping")
    for field in ("id", "provenance", "version", "license", "availability_status"):
        if not data.get(field):
            raise ValueError(f"manifest record requires {field}")
    if data.get("id", "").split(":", 1)[0] in {"dataset", "repository"} and not data.get("reference_version"):
        raise ValueError("external reference manifest requires reference_version")
    return _validate_candidate(load_record(data))


def load_candidate_manifest(path: str | Path) -> list[ManifestRecord]:
    """Load a candidate-only YAML manifest with unique stable IDs."""
    try:
        data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"cannot read manifest YAML: {error}") from error
    if not isinstance(data, dict) or not isinstance(data.get("records"), list):
        raise ValueError("manifest requires a records list")
    records = [_load_candidate(item) for item in data["records"]]
    if len({record.id for record in records}) != len(records):
        raise ValueError("manifest requires unique stable IDs")
    return sorted(records, key=lambda record: record.id)


def write_candidate_manifest(path: str | Path, records: list[ManifestRecord]) -> None:
    """Write a stable-ID-sorted canonical candidate manifest."""
    checked = [_validate_candidate(record) for record in records]
    if len({record.id for record in checked}) != len(checked):
        raise ValueError("manifest requires unique stable IDs")
    content = yaml.safe_dump(
        {"records": [record.model_dump(mode="json") for record in sorted(checked, key=lambda record: record.id)]},
        allow_unicode=True, sort_keys=True,
    )
    Path(path).write_text(content, encoding="utf-8")


def _bundle_record(row: dict, provenance: str, imported_on: date) -> ManifestRecord:
    missing = [key for key in ("id", "title", "url", "license", "version") if not row.get(key)]
    kind = row.get("kind")
    if kind == "paper":
        missing += [key for key in ("authors", "venue", "publication_type", "keywords") if not row.get(key)]
        if not missing:
            identifier = f"source:{row['id']}"
            authors = [{"id": f"author:{row['id']}-{index}", "name": name, "provenance": provenance,
                        "version": row["version"]} for index, name in enumerate(row["authors"], 1)]
            return Source(id=identifier, title=row["title"], authors=authors, year=row["year"], doi=row.get("doi"),
                          url=row["url"], venue=row["venue"], publication_type=row["publication_type"],
                          domains=row["domains"], keywords=row["keywords"], access_date=imported_on,
                          availability_status="external_only", license=row["license"], provenance=provenance,
                          version=row["version"])
    elif kind in {"dataset", "repository"}:
        missing += [key for key in ("canonical_source", "reference_version") if not row.get(key)]
        if not missing:
            model = DatasetReference if kind == "dataset" else RepositoryReference
            return model(id=f"{kind}:{row['id']}", canonical_source=row["canonical_source"], url=row["url"],
                         reference_version=row["reference_version"], acquisition_date=imported_on,
                         availability_status="external_only", license=row["license"], provenance=provenance,
                         version=row["version"])
    if kind not in {"paper", "dataset", "repository"}:
        missing.append("supported kind")
    raise ValueError(", ".join(sorted(set(missing))))


def prepare_bundle_candidates(bundle: str | Path, manifest_path: str | Path, report_path: str | Path,
                              cap: int = DEFAULT_BUNDLE_IMPORT_CAP) -> dict:
    """Fail closed while preparing a capped, candidate-only source bundle."""
    if cap < 1:
        raise ValueError("import cap must be positive")
    root = Path(bundle)
    inventories = ["research/sources/source_catalog.jsonl", "research/corpus/seed-manifest.yaml",
                   "research/knowledge/nodes.jsonl", "research/knowledge/edges.jsonl"]
    package = json.loads((root / "MANIFEST.json").read_text(encoding="utf-8"))
    checksums = {entry["path"]: entry["sha256"] for entry in package["files"]}
    if any(path not in checksums for path in inventories):
        raise ValueError("bundle manifest lacks required inventory")
    generated = date.fromisoformat(package["generated"])
    catalog = [json.loads(line) for line in (root / inventories[0]).read_text(encoding="utf-8").splitlines() if line]
    candidates, rejected = [], []
    catalog.sort(key=lambda item: item["id"])
    selected = [next((row for row in catalog if row.get("kind") == kind), None)
                for kind in ("paper", "dataset", "repository")]
    selected = [row for row in selected if row] + [row for row in catalog if row not in selected]
    for row in selected[:cap]:
        provenance = f"{root.as_posix()}/{inventories[0]}#{row['id']}"
        try:
            candidates.append(_bundle_record(row, provenance, generated))
        except ValueError as error:
            rejected.append({"source_id": row.get("id", "unknown"), "reason": str(error)})
    write_candidate_manifest(manifest_path, candidates)
    report = {"parent_bundle": root.as_posix(), "generation_date": generated.isoformat(), "import_cap": cap,
              "decision": "candidate_only_fail_closed", "inventory_checksums": {path: checksums[path] for path in inventories},
              "candidate_ids": [record.id for record in sorted(candidates, key=lambda item: item.id)], "rejections": rejected}
    Path(report_path).write_text(yaml.safe_dump(report, sort_keys=True), encoding="utf-8")
    return report
