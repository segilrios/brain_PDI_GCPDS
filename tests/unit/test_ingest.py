from datetime import date

import pytest

from semillero_kb.ingest import ingest_local_document
from semillero_kb.models import EvidenceLocator


def test_local_heading_ingestion_builds_unverified_candidate_inputs(tmp_path):
    document = tmp_path / "authorized" / "notes.txt"
    document.parent.mkdir(); document.write_text("Title\nMethods\nBounded local observation.", encoding="utf-8")
    locator = EvidenceLocator(kind="heading_anchor", coordinates={"heading": "Methods"})
    candidate = ingest_local_document(document, authorized_root=document.parent, source_id="source:local",
                                      locator=locator, max_excerpt_chars=64)
    evidence = candidate.evidence_input("evidence:local", assessor="curator:ada", assessed_on=date(2026, 8, 31))
    claim = candidate.claim_input("claim:local", extracted_on=date(2026, 8, 31))
    assert candidate.local_path == "notes.txt" and candidate.excerpt == "Methods\nBounded local observation."
    assert candidate.locator.excerpt_checksum.startswith("sha256:")
    assert evidence.admission_state == claim.admission_state == "candidate"
    assert claim.verification_status == "unverified" and claim.confidence == 0.0
    assert evidence.provenance == claim.provenance == "local:notes.txt#source=source:local"


@pytest.mark.parametrize("path_name, locator, message", [
    ("../outside.txt", EvidenceLocator(kind="heading_anchor", coordinates={"heading": "x"}), "outside"),
    ("missing.txt", EvidenceLocator(kind="heading_anchor", coordinates={"heading": "x"}), "missing"),
    ("paper.pdf", EvidenceLocator(kind="pdf_page_section", coordinates={"page": "1", "section": "Intro"}), "optional pypdf"),
])
def test_local_ingestion_fails_closed_for_unauthorized_missing_or_unavailable_pdf(tmp_path, path_name, locator, message):
    root = tmp_path / "authorized"; root.mkdir()
    if path_name == "../outside.txt":
        (tmp_path / "outside.txt").write_text("x", encoding="utf-8")
    if path_name == "paper.pdf":
        (root / path_name).write_bytes(b"not a PDF")
    with pytest.raises(ValueError, match=message):
        ingest_local_document(root / path_name, authorized_root=root, source_id="source:local", locator=locator)
