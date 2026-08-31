"""Fail-closed human curation transitions for canonical records."""
from datetime import datetime

from .models import AdmissionState, AssertionType, Claim, CurationEvent, Record, VerificationStatus


def curate_record(record: Record, *, curator: str, rationale: str, curated_at: datetime | str) -> Record:
    """Admit a candidate as a human-selected seed without asserting truth."""
    if record.admission_state is not AdmissionState.CANDIDATE:
        raise ValueError("only candidates can be curated as human seeds")
    return _transition(record, AdmissionState.HUMAN_SEED, curator, rationale, curated_at, [])


def promote_record(record: Record, *, curator: str, rationale: str, curated_at: datetime | str,
                   validation_evidence: list[str]) -> Record:
    """Promote a curated seed only after recorded validation evidence."""
    if record.admission_state is not AdmissionState.HUMAN_SEED:
        raise ValueError("only human seeds can be promoted")
    if isinstance(record, Claim) and (record.assertion_type is AssertionType.INFERENCE
                                      or record.verification_status is VerificationStatus.UNVERIFIED):
        raise ValueError("unverified or inferred claims cannot become verified expansions")
    return _transition(record, AdmissionState.VERIFIED_EXPANSION, curator, rationale, curated_at, validation_evidence)


def _transition(record: Record, target: AdmissionState, curator: str, rationale: str,
                curated_at: datetime | str, validation_evidence: list[str]) -> Record:
    data = record.model_dump(mode="python")
    data["admission_state"] = target
    data["curation_history"] = [*record.curation_history, CurationEvent(
        source_state=record.admission_state, target_state=target, curator=curator,
        curated_at=curated_at, rationale=rationale, validation_evidence=validation_evidence,
    )]
    return type(record).model_validate(data)
