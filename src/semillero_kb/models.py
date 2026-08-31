"""Validated records; durable scientific data remains in Git-managed YAML."""
from datetime import date
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

StableId = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*:[a-z0-9][a-z0-9._-]*$")]


class Lifecycle(StrEnum):
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    SUPERSEDED = "superseded"
    RETRACTED = "retracted"


class AssertionType(StrEnum):
    OBSERVATION = "observation"
    CLAIM = "claim"
    INFERENCE = "inference"
    HYPOTHESIS = "hypothesis"
    EXPERIMENTAL_RESULT = "experimental_result"


class VerificationStatus(StrEnum):
    UNVERIFIED = "unverified"
    SOURCE_VERIFIED = "source_verified"
    CROSS_VERIFIED = "cross_verified"
    EXPERIMENTALLY_VERIFIED = "experimentally_verified"
    CONTRADICTED = "contradicted"
    INCONCLUSIVE = "inconclusive"


class AvailabilityStatus(StrEnum):
    AVAILABLE_LOCAL = "available_local"
    EXTERNAL_ONLY = "external_only"
    UNAVAILABLE = "unavailable"


class LocatorKind(StrEnum):
    PDF_PAGE_SECTION = "pdf_page_section"
    HEADING_ANCHOR = "heading_anchor"
    TIMESTAMP = "timestamp"
    GIT_LINES = "git_lines"
    DATASET_RECORD = "dataset_record"
    FIGURE_TABLE_EQUATION = "figure_table_equation"
    URI_FRAGMENT = "uri_fragment"


class EvidenceLocator(BaseModel):
    kind: LocatorKind
    coordinates: dict[str, str]
    excerpt_checksum: str | None = None

    @model_validator(mode="after")
    def has_coordinates(self):
        required = {
            LocatorKind.PDF_PAGE_SECTION: {"page", "section"},
            LocatorKind.HEADING_ANCHOR: {"heading"}, LocatorKind.TIMESTAMP: {"timestamp"},
            LocatorKind.GIT_LINES: {"path", "start_line", "end_line"},
            LocatorKind.DATASET_RECORD: {"record_id"},
            LocatorKind.FIGURE_TABLE_EQUATION: {"label"}, LocatorKind.URI_FRAGMENT: {"fragment"},
        }[self.kind]
        if not required <= self.coordinates.keys() or any(not value for value in self.coordinates.values()):
            raise ValueError(f"{self.kind} requires coordinates: {', '.join(sorted(required))}")
        return self


class Record(BaseModel):
    id: StableId
    provenance: str
    version: int = Field(ge=1)
    lifecycle: Lifecycle = Lifecycle.ACTIVE
    predecessor_id: StableId | None = None
    lifecycle_reason: str | None = None
    lifecycle_date: date | None = None
    lifecycle_actor: str | None = None

    @model_validator(mode="after")
    def preserves_lifecycle_history(self):
        if self.lifecycle is not Lifecycle.ACTIVE and not all((self.predecessor_id, self.lifecycle_reason, self.lifecycle_date, self.lifecycle_actor)):
            raise ValueError("non-active records require predecessor, reason, date, and actor")
        return self


class Author(Record):
    name: str = Field(min_length=1)
    kind: str | None = None
    identifier: str | None = None


class Source(Record):
    title: str = Field(min_length=1)
    authors: list[Author] = Field(min_length=1)
    year: int = Field(ge=0)
    doi: str | None = None
    url: str | None = None
    venue: str = Field(min_length=1)
    publication_type: str = Field(min_length=1)
    domains: list[str] = Field(min_length=1)
    keywords: list[str] = Field(min_length=1)
    access_date: date
    availability_status: AvailabilityStatus
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    license: str | None = None
    local_path: str | None = None
    checksum: str | None = None


class Evidence(Record):
    source_id: StableId | None = None
    result_id: StableId | None = None
    locator: EvidenceLocator
    role: str = Field(min_length=1)
    stance: str = Field(min_length=1)
    assessor: str = Field(min_length=1)
    assessment_date: date
    rationale: str = Field(min_length=1)

    @model_validator(mode="after")
    def binds_one_subject(self):
        if (self.source_id is None) == (self.result_id is None):
            raise ValueError("evidence requires exactly one source_id or result_id")
        return self


class Entity(Record):
    entity_type: str = Field(min_length=1)
    label: str = Field(min_length=1)


class Relation(Record):
    subject_id: StableId
    predicate: str = Field(min_length=1)
    object_id: StableId
    directed: bool = True


class ExternalReference(Record):
    canonical_source: str = Field(min_length=1)
    url: str = Field(min_length=1)
    reference_version: str = Field(min_length=1)
    license: str | None = None
    acquisition_date: date
    availability_status: AvailabilityStatus
    local_path: str | None = None
    checksum: str | None = None


class DatasetReference(ExternalReference):
    pass


class RepositoryReference(ExternalReference):
    pass


class Claim(Record):
    statement: str = Field(min_length=1)
    source_id: StableId
    locator: EvidenceLocator
    extraction_date: date
    assertion_type: AssertionType
    confidence: float = Field(ge=0, le=1)
    confidence_rationale: str = Field(min_length=1)
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    @model_validator(mode="after")
    def blocks_unsupported_promotion(self):
        if self.assertion_type is AssertionType.INFERENCE and self.verification_status is not VerificationStatus.UNVERIFIED:
            raise ValueError("an inference cannot self-promote to verified")
        return self
