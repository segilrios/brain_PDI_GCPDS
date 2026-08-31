"""Canonical YAML serialization and typed record loading."""
from pathlib import Path

import yaml
from pydantic import BaseModel, ValidationError

from . import models

_RECORD_TYPES = {
    "author": models.Author, "source": models.Source, "evidence": models.Evidence,
    "entity": models.Entity, "relation": models.Relation, "claim": models.Claim,
    "experiment": models.Experiment, "result": models.Result,
    "dataset": models.DatasetReference, "datasetreference": models.DatasetReference,
    "repository": models.RepositoryReference, "repositoryreference": models.RepositoryReference,
}


def load_yaml(path: str | Path) -> BaseModel:
    """Load one canonical YAML record selected by its stable ID prefix."""
    path = Path(path)
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        raise ValueError(f"cannot read YAML: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("record must be a YAML mapping")
    identifier = data.get("id")
    if not isinstance(identifier, str) or ":" not in identifier:
        raise ValueError("record requires a stable id with a type prefix")
    record_type = _RECORD_TYPES.get(identifier.split(":", 1)[0])
    if record_type is None:
        raise ValueError(f"unknown record type prefix: {identifier.split(':', 1)[0]}")
    try:
        return record_type.model_validate(data)
    except ValidationError as error:
        raise ValueError(f"invalid {record_type.__name__} record: {error}") from error


def dump_yaml(record: BaseModel) -> str:
    """Serialize a typed record deterministically for Git review."""
    return yaml.safe_dump(record.model_dump(mode="json"), allow_unicode=True, sort_keys=True)