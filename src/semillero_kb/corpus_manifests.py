"""Canonical candidate manifests for source and external-reference metadata."""
from pathlib import Path

import yaml
from pydantic import BaseModel

from .models import AdmissionState, DatasetReference, RepositoryReference, Source
from .yaml_records import load_record

ManifestRecord = Source | DatasetReference | RepositoryReference


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
