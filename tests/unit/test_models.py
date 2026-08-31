import json
from datetime import date
from pathlib import Path

import pytest
from pydantic import ValidationError

from semillero_kb.models import Claim, EvidenceLocator, Lifecycle, Record
from semillero_kb.validation import ResearchDomain, claim_json_schema, validate_domain_relation


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
