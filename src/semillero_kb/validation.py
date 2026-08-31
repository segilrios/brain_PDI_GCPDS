"""Fail-closed semantic safeguards outside the storage and graph layers."""
from enum import StrEnum

from .models import Claim


class ResearchDomain(StrEnum):
    SURFACE_WATER = "surface_water_observation"
    GROUNDWATER = "groundwater_potential_mapping"
    GEOTHERMAL_PROXY = "geothermal_surface_proxy"
    RESERVOIR = "geothermal_reservoir"


def claim_json_schema() -> dict:
    """Return the portable JSON Schema generated from the authoritative model."""
    return Claim.model_json_schema()


def validate_domain_relation(subject: ResearchDomain, predicate: str, object_: ResearchDomain) -> None:
    forbidden = {
        (ResearchDomain.SURFACE_WATER, "indicates", ResearchDomain.GROUNDWATER),
        (ResearchDomain.SURFACE_WATER, "confirms", ResearchDomain.GROUNDWATER),
        (ResearchDomain.GEOTHERMAL_PROXY, "confirms", ResearchDomain.RESERVOIR),
    }
    if (subject, predicate, object_) in forbidden:
        raise ValueError("domain firewall rejects this unqualified relation")
