import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from semillero_kb.models import (
    Author, AvailabilityStatus, Claim, DatasetReference, Entity, Evidence, EvidenceLocator,
    Experiment, Lifecycle, Record, Relation, RepositoryReference, Result, Source,
)
from semillero_kb.validation import (
    ResearchDomain, claim_json_schema, experiment_json_schemas, reference_json_schemas, validate_domain_relation,
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
    record = Record(id="record:old", provenance="test", version=1, lifecycle=Lifecycle.RETRACTED, predecessor_id="record:new", lifecycle_reason="corrected", lifecycle_date=date.today(), lifecycle_actor="curator")
    assert record.lifecycle is Lifecycle.RETRACTED


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
