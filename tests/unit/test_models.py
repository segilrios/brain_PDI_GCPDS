import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from semillero_kb.models import (
    AdmissionState, Author, AvailabilityStatus, Claim, CurationEvent, DatasetReference, Entity, Evidence, EvidenceLocator,
    Experiment, Lifecycle, LifecycleTransition, Record, Relation, RepositoryReference, Result, Source,
)
from semillero_kb.curation import curate_record, promote_record
from semillero_kb.validation import (
    ResearchDomain, claim_json_schema, experiment_json_schemas, reference_json_schemas, transition_record,
    validate_domain_relation,
)


def payload():
    return json.loads((Path(__file__).parents[1] / "fixtures" / "valid_claim.json").read_text())


def test_synthetic_claim_is_valid_and_schema_is_portable():
    claim = Claim.model_validate(payload())
    assert claim.confidence == 0.7
    assert "verification_status" in claim_json_schema()["properties"]


@pytest.mark.parametrize("field,value", [("id", "bad id"), ("confidence", 1.2), ("verification_status", "source_verified")])
def test_epistemic_fields_are_validated(field, value):
    data = payload(); data[field] = value
    if field == "verification_status": data["assertion_type"] = "inference"
    with pytest.raises(ValidationError): Claim.model_validate(data)


def test_locator_and_lifecycle_are_fail_closed():
    with pytest.raises(ValidationError): EvidenceLocator(kind="pdf_page_section", coordinates={"page": "1"})
    with pytest.raises(ValidationError): Record(id="record:old", provenance="test", version=1, lifecycle=Lifecycle.RETRACTED)
    with pytest.raises(ValidationError): LifecycleTransition(
        previous_state=Lifecycle.ACTIVE, next_state=Lifecycle.SUPERSEDED,
        actor="curator", transition_date=date.today(), reason="corrected",
    )


def test_domain_firewall_rejects_conflation():
    with pytest.raises(ValueError): validate_domain_relation(ResearchDomain.SURFACE_WATER, "indicates", ResearchDomain.GROUNDWATER)
    with pytest.raises(ValueError): validate_domain_relation(ResearchDomain.GEOTHERMAL_PROXY, "confirms", ResearchDomain.RESERVOIR)


def record_data(id_: str) -> dict:
    return {"id": id_, "provenance": "synthetic fixture", "version": 1}


def test_source_evidence_entity_and_relation_contracts_preserve_provenance():
    author = Author(**record_data("author:ada"), name="Ada")
    source = Source(**record_data("source:paper"), title="Paper", authors=[author], year=2026,
                    venue="Journal", publication_type="article", domains=["hydrology"], keywords=["water"],
                    access_date=date.today(), availability_status="external_only")
    evidence = Evidence(**record_data("evidence:paper-p1"), source_id=source.id,
                        locator=EvidenceLocator(kind="pdf_page_section", coordinates={"page": "1", "section": "Methods"}),
                        role="supporting", stance="supports", assessor="curator", assessment_date=date.today(), rationale="Direct observation")
    entity = Entity(**record_data("entity:water"), entity_type="Concept", label="Water")
    relation = Relation(**record_data("relation:uses"), subject_id=entity.id, predicate="uses", object_id="method:rs")
    assert (evidence.source_id, relation.directed, source.provenance) == (source.id, True, "synthetic fixture")


@pytest.mark.parametrize("reference", [DatasetReference, RepositoryReference])
def test_external_references_need_metadata_not_local_bytes(reference):
    value = reference(**record_data(f"{reference.__name__.lower()}:remote"), canonical_source="DOI:10.1/example",
                      url="https://example.test/resource", reference_version="v1", acquisition_date=date.today(),
                      availability_status=AvailabilityStatus.EXTERNAL_ONLY)
    assert value.local_path is value.checksum is None
    assert reference.__name__ in reference_json_schemas()


def test_stable_ids_and_evidence_binding_are_fail_closed():
    with pytest.raises(ValidationError): Entity(**record_data("invalid id"), entity_type="Concept", label="Bad")
    with pytest.raises(ValidationError): Evidence(**record_data("evidence:ambiguous"), source_id="source:x", result_id="result:x",
        locator=EvidenceLocator(kind="uri_fragment", coordinates={"fragment": "part"}), role="supporting", stance="supports",
        assessor="curator", assessment_date=date.today(), rationale="Cannot bind twice")


def test_reviewed_spo_projection_matches_canonical_claim_and_promotes():
    data = payload() | {"statement": "Surface water supports observation.", "subject": "Surface water",
                        "predicate": "supports", "object": "observation", "spo_equivalence_reviewed": True,
                        "spo_equivalence_statement": "Surface water supports observation.",
                        "verification_status": "source_verified"}
    assert Claim.model_validate(data).verification_status == "source_verified"


@pytest.mark.parametrize("overrides", [
    {"spo_equivalence_reviewed": True, "spo_equivalence_statement": "Contradictory statement."},
    {"spo_equivalence_reviewed": False, "verification_status": "source_verified"},
])
def test_inconsistent_or_unreviewed_spo_blocks_promotion(overrides):
    data = payload() | {"subject": "Surface water", "predicate": "supports", "object": "observation"} | overrides
    with pytest.raises(ValidationError): Claim.model_validate(data)


def test_confidence_and_verification_status_remain_independent():
    data = payload() | {"confidence": 0.1, "verification_status": "source_verified"}
    assert Claim.model_validate(data).confidence == 0.1


def test_experiment_supports_multiple_distinct_results():
    data = json.loads((Path(__file__).parents[1] / "fixtures" / "valid_experiment.json").read_text())
    experiment = Experiment.model_validate(data)
    results = [Result(**record_data("result:one"), experiment_id=experiment.id, status="positive",
                      outputs=["output:one"], metrics={"accuracy": 0.9}, limitations=["synthetic"], execution_date=date.today()),
               Result(**record_data("result:two"), experiment_id=experiment.id, status="inconclusive",
                      outputs=["output:two"], limitations=["small sample"], execution_date=date.today())]
    assert {result.status for result in results} == {"positive", "inconclusive"}
    assert all(result.experiment_id == experiment.id for result in results)
    assert {"positive", "negative", "inconclusive", "failed"} <= set(Result.model_fields["status"].annotation)
    assert set(experiment_json_schemas()) == {"Experiment", "Result"}


def test_lifecycle_transitions_preserve_history_and_retractions():
    record = Record(id="record:obsolete", provenance="test", version=1)
    deprecated = transition_record(record, Lifecycle.DEPRECATED, actor="curator", reason="obsolete", transition_date=date.today())
    retracted = transition_record(deprecated, Lifecycle.RETRACTED, actor="editor", reason="invalid evidence", transition_date=date.today())
    assert record.lifecycle is Lifecycle.ACTIVE
    assert [(item.previous_state, item.next_state) for item in retracted.lifecycle_history] == [
        (Lifecycle.ACTIVE, Lifecycle.DEPRECATED), (Lifecycle.DEPRECATED, Lifecycle.RETRACTED),
    ]
    assert retracted.lifecycle_history[-1].reason == "invalid evidence"


def test_supersession_requires_successor_and_explicit_version_predecessor():
    record = Record(id="record:old", provenance="test", version=1)
    superseded = transition_record(record, Lifecycle.SUPERSEDED, actor="curator", reason="revised", transition_date=date.today(), successor_id="record:new")
    successor = Record(id="record:new", provenance="test", version=2, predecessor_id=record.id)
    assert superseded.lifecycle_history[-1].successor_id == successor.id
    assert transition_record(successor, Lifecycle.DEPRECATED, actor="curator", reason="old draft", transition_date=date.today()).lifecycle_history[-1].predecessor_id == record.id
    with pytest.raises(ValidationError): Record(id="record:missing-link", provenance="test", version=2)


def test_invalid_lifecycle_transitions_fail_closed_without_delete_api():
    retracted = transition_record(Record(id="record:kept", provenance="test", version=1), Lifecycle.RETRACTED,
                                  actor="curator", reason="invalid", transition_date=date.today())
    with pytest.raises(ValueError): transition_record(retracted, Lifecycle.ACTIVE, actor="curator", reason="restore", transition_date=date.today())
    assert not hasattr(__import__("semillero_kb.validation", fromlist=["delete_record"]), "delete_record")


def test_curation_requires_human_seed_and_preserves_audit_history():
    candidate = Record(**record_data("record:candidate"))
    seed = curate_record(candidate, curator="curator:ada", rationale="Selected for relevance", curated_at=date.today())
    verified = promote_record(seed, curator="curator:ada", rationale="Identity and scope checked",
                              curated_at=date.today(), validation_evidence=["evidence:review"])
    assert candidate.admission_state is AdmissionState.CANDIDATE
    assert seed.admission_state is AdmissionState.HUMAN_SEED
    assert verified.admission_state is AdmissionState.VERIFIED_EXPANSION
    assert [(event.source_state, event.target_state, event.curator) for event in verified.curation_history] == [
        (AdmissionState.CANDIDATE, AdmissionState.HUMAN_SEED, "curator:ada"),
        (AdmissionState.HUMAN_SEED, AdmissionState.VERIFIED_EXPANSION, "curator:ada"),
    ]
    conflict = Claim.model_validate(payload() | {"verification_status": "contradicted"})
    assert curate_record(conflict, curator="curator:ada", rationale="Keep conflicting evidence", curated_at=date.today()).verification_status == "contradicted"


def test_curation_blocks_self_promotion_inference_and_missing_evidence():
    candidate = Record(**record_data("record:candidate"))
    with pytest.raises(ValueError, match="human seeds"): promote_record(
        candidate, curator="curator:ada", rationale="skip", curated_at=date.today(), validation_evidence=["evidence:x"])
    with pytest.raises(ValidationError, match="curation transition"): Record(**record_data("record:bad"),
        admission_state="verified_expansion", curation_history=[CurationEvent(
            source_state="candidate", target_state="verified_expansion", curator="curator:ada",
            curated_at=date.today(), rationale="invalid", validation_evidence=["evidence:x"])])
    inference = Claim.model_validate(payload() | {"assertion_type": "inference"})
    seed = curate_record(inference, curator="curator:ada", rationale="Relevant lead", curated_at=date.today())
    with pytest.raises(ValueError, match="inferred"): promote_record(
        seed, curator="curator:ada", rationale="automated", curated_at=date.today(), validation_evidence=["evidence:x"])
