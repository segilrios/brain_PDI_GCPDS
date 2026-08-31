"""Fail-closed semantic safeguards outside the storage and graph layers."""
from datetime import date
from enum import StrEnum

from .models import (
    Claim, DatasetReference, Experiment, Lifecycle, LifecycleTransition, Record,
    RepositoryReference, Result, Source,
)


class ResearchDomain(StrEnum):
    SURFACE_WATER = "surface_water_observation"
    GROUNDWATER = "groundwater_potential_mapping"
    GEOTHERMAL_PROXY = "geothermal_surface_proxy"
    RESERVOIR = "geothermal_reservoir"


def claim_json_schema() -> dict:
    """Return the portable JSON Schema generated from the authoritative model."""
    return Claim.model_json_schema()


def reference_json_schemas() -> dict[str, dict]:
    """Return portable schemas for records that may only exist externally."""
    return {model.__name__: model.model_json_schema() for model in (Source, DatasetReference, RepositoryReference)}


def experiment_json_schemas() -> dict[str, dict]:
    """Return portable schemas for linked experiment and result records."""
    return {model.__name__: model.model_json_schema() for model in (Experiment, Result)}


def transition_record(
    record: Record, next_state: Lifecycle, *, actor: str, reason: str,
    transition_date: date | str, successor_id: str | None = None,
) -> Record:
    """Return a new record with one validated, append-only lifecycle transition."""
    if successor_id == record.id:
        raise ValueError("a record cannot supersede itself")
    transition = LifecycleTransition(
        previous_state=record.lifecycle, next_state=next_state, actor=actor,
        transition_date=transition_date, reason=reason, predecessor_id=record.predecessor_id,
        successor_id=successor_id,
    )
    data = record.model_dump(mode="python")
    data["lifecycle"] = next_state
    data["lifecycle_history"] = [*record.lifecycle_history, transition]
    return type(record).model_validate(data)


def validate_domain_relation(subject: ResearchDomain, predicate: str, object_: ResearchDomain) -> None:
    forbidden = {
        (ResearchDomain.SURFACE_WATER, "indicates", ResearchDomain.GROUNDWATER),
        (ResearchDomain.SURFACE_WATER, "confirms", ResearchDomain.GROUNDWATER),
        (ResearchDomain.GEOTHERMAL_PROXY, "confirms", ResearchDomain.RESERVOIR),
    }
    if (subject, predicate, object_) in forbidden:
        raise ValueError("domain firewall rejects this unqualified relation")
