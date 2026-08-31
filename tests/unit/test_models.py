import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from semillero_kb.models import (
    Author, AvailabilityStatus, Claim, DatasetReference, Entity, Evidence, EvidenceLocator,
    Lifecycle, Record, Relation, RepositoryReference, Source,
)
from semillero_kb.validation import (
    ResearchDomain, claim_json_schema, reference_json_schemas, validate_domain_relation,
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
