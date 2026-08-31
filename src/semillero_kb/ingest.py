"""Bounded, local-only extraction for unverified evidence and claim candidates."""
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from pathlib import Path

from .models import AdmissionState, AssertionType, Claim, Evidence, EvidenceLocator, LocatorKind, VerificationStatus

_TEXT_SUFFIXES = {".txt", ".md"}
_MAX_SCAN_CHARS = 32_768


@dataclass(frozen=True)
class LocalIngestionCandidate:
    """A bounded excerpt that cannot assert truth or bypass human curation."""

    source_id: str
    local_path: str
    provenance: str
    locator: EvidenceLocator
    excerpt: str
    admission_state: AdmissionState = AdmissionState.CANDIDATE
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    def evidence_input(self, evidence_id: str, *, assessor: str, assessed_on: date) -> Evidence:
        return Evidence(id=evidence_id, provenance=self.provenance, version=1, source_id=self.source_id,
                        locator=self.locator, role="candidate_excerpt", stance="unverified", assessor=assessor,
                        assessment_date=assessed_on, rationale="Local extraction awaiting human review")

    def claim_input(self, claim_id: str, *, extracted_on: date) -> Claim:
        return Claim(id=claim_id, provenance=self.provenance, version=1, source_id=self.source_id,
                     locator=self.locator, statement=self.excerpt, extraction_date=extracted_on,
                     assertion_type=AssertionType.OBSERVATION, confidence=0.0,
                     confidence_rationale="Local excerpt candidate; no scientific truth asserted")


def ingest_local_document(path: str | Path, *, authorized_root: str | Path, source_id: str,
                          locator: EvidenceLocator, max_excerpt_chars: int = 1_000) -> LocalIngestionCandidate:
    """Extract one bounded local excerpt; network, promotion, and expansion are absent."""
    if locator.kind not in {LocatorKind.PDF_PAGE_SECTION, LocatorKind.HEADING_ANCHOR}:
        raise ValueError("local ingestion requires a pdf_page_section or heading_anchor locator")
    if not 1 <= max_excerpt_chars <= 4_096:
        raise ValueError("max_excerpt_chars must be between 1 and 4096")
    root = Path(authorized_root).resolve()
    try:
        document = Path(path).resolve(strict=True)
        relative_path = document.relative_to(root)
    except FileNotFoundError as error:
        raise ValueError("local document is missing or unreadable") from error
    except ValueError as error:
        raise ValueError("local document path is outside the authorized root") from error
    if not document.is_file():
        raise ValueError("local document path must be a readable file")
    excerpt = _extract(document, locator, max_excerpt_chars)
    if not excerpt:
        raise ValueError("local document locator produced an empty excerpt")
    checked_locator = locator.model_copy(update={"excerpt_checksum": f"sha256:{sha256(excerpt.encode()).hexdigest()}"})
    provenance = f"local:{relative_path.as_posix()}#source={source_id}"
    return LocalIngestionCandidate(source_id, relative_path.as_posix(), provenance, checked_locator, excerpt)


def _extract(document: Path, locator: EvidenceLocator, limit: int) -> str:
    if document.suffix.lower() == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as error:
            raise ValueError("PDF extraction requires the optional pypdf dependency") from error
        try:
            page = int(locator.coordinates["page"])
            text = PdfReader(document).pages[page - 1].extract_text() or ""
        except (IndexError, OSError, ValueError) as error:
            raise ValueError("local PDF page is unreadable") from error
    elif document.suffix.lower() in _TEXT_SUFFIXES:
        try:
            with document.open(encoding="utf-8") as handle:
                text = handle.read(_MAX_SCAN_CHARS)
        except (OSError, UnicodeError) as error:
            raise ValueError("local text document is unreadable") from error
    else:
        raise ValueError("local ingestion supports only PDF, .txt, or .md documents")
    if locator.kind is LocatorKind.HEADING_ANCHOR:
        heading = locator.coordinates["heading"]
        start = text.find(heading)
        if start < 0:
            raise ValueError("heading anchor was not found in bounded local scan")
        text = text[start:]
    return text.strip()[:limit]
