from datetime import date

from semillero_kb.models import Claim, EvidenceLocator, Source
from semillero_kb.search import build_index, canonical_yaml, csl_json, graph_json, query_index


def record(id_, **fields):
    return {"id": id_, "provenance": "fixture", "version": 1} | fields


def records():
    source = Source(**record("source:zeta", title="Water & heat", authors=[record("author:ada", name="Ada")], year=2026,
        doi="10.1/example", venue="Journal", publication_type="article", domains=["surface_water"], keywords=["water"],
        access_date=date(2026, 1, 1), availability_status="external_only"))
    locator = EvidenceLocator(kind="pdf_page_section", coordinates={"page": "1", "section": "Results"})
    claim = Claim(**record("claim:alpha", statement="Water is observed.", source_id=source.id, locator=locator,
        extraction_date=date(2026, 1, 1), assertion_type="claim", confidence=.8, confidence_rationale="Synthetic"))
    return [claim, source]


def test_rebuild_query_is_stable_and_special_characters_are_safe(tmp_path):
    index = tmp_path / "search.sqlite"
    build_index(records(), index)
    first = index.read_bytes()
    assert query_index(index, 'water: AND (heat) "*', limit=999) == ["source:zeta"]
    build_index(reversed(records()), index)
    assert index.read_bytes() == first


def test_exports_are_sorted_derived_and_do_not_mutate_records():
    data = records()
    before = [record.model_dump() for record in data]
    assert graph_json(data) == graph_json(reversed(data))
    assert '"id":"source:zeta"' in csl_json(data) and '"DOI":"10.1/example"' in csl_json(data)
    assert canonical_yaml(data)["source:zeta"] == canonical_yaml(reversed(data))["source:zeta"]
    assert [record.model_dump() for record in data] == before
