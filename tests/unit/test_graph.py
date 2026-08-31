from datetime import date

from semillero_kb.graph import build_graph, contradictions, neighbors, provenance, selected_subgraph
from semillero_kb.models import Claim, Entity, Evidence, EvidenceLocator, Relation, Source, VerificationStatus


def record(id_, **fields):
    return {"id": id_, "provenance": "fixture", "version": 1} | fields


def graph_fixture():
    source = Source(**record("source:paper", title="Paper", authors=[record("author:ada", name="Ada")], year=2026,
        venue="Journal", publication_type="article", domains=["surface_water_observation"], keywords=["water"],
        access_date=date.today(), availability_status="external_only"))
    evidence = Evidence(**record("evidence:p1", source_id=source.id, locator=EvidenceLocator(kind="pdf_page_section",
        coordinates={"page": "1", "section": "Results"}), role="supporting", stance="supports", assessor="curator:ada",
        assessment_date=date.today(), rationale="Synthetic locator"))
    claim = Claim(**record("claim:water", provenance=evidence.id, statement="Water is observed.", source_id=source.id,
        locator=evidence.locator, extraction_date=date.today(), assertion_type="claim", confidence=.8,
        confidence_rationale="Synthetic", verification_status="source_verified"))
    conflict = Claim(**record("claim:conflict", statement="Water is not observed.", source_id=source.id,
        locator=evidence.locator, extraction_date=date.today(), assertion_type="claim", confidence=.4,
        confidence_rationale="Synthetic", verification_status=VerificationStatus.CONTRADICTED))
    water = Entity(**record("entity:water", entity_type="Concept", label="Water"))
    method = Entity(**record("method:eo", entity_type="Method", label="EO"))
    return [source, evidence, claim, conflict, water, method,
        Relation(**record("relation:uses", provenance=claim.id, subject_id=water.id, predicate="uses", object_id=method.id)),
        Relation(**record("relation:measures", provenance=claim.id, subject_id=water.id, predicate="measures", object_id=method.id))]


def test_multigraph_preserves_directed_parallel_relations_and_record_metadata():
    graph = build_graph(graph_fixture())
    assert graph.is_multigraph() and graph.has_edge("entity:water", "method:eo", "relation:uses")
    assert graph.has_edge("entity:water", "method:eo", "relation:measures")
    assert not graph.has_edge("method:eo", "entity:water", "relation:uses")
    assert graph.nodes["claim:water"]["lifecycle"] == "active"


def test_provenance_is_bidirectional_and_deterministic_without_inventing_records():
    graph = build_graph(graph_fixture())
    assert provenance(graph, "source:paper") == ["claim:conflict", "claim:water", "evidence:p1", "relation:measures", "relation:uses"]
    assert provenance(graph, "relation:uses", reverse=True) == ["claim:water", "evidence:p1", "source:paper"]
    assert neighbors(graph, "entity:water") == ["method:eo"]
    assert neighbors(graph, "method:eo", direction="in") == ["entity:water"]


def test_contradictions_and_selected_subgraph_are_stable_and_firewall_agnostic():
    graph = build_graph(graph_fixture())
    assert contradictions(graph) == ["claim:conflict"]
    subgraph = selected_subgraph(graph, ["method:eo", "entity:water", "method:eo"])
    assert list(subgraph.nodes) == ["entity:water", "method:eo"]
    assert list(subgraph.edges(keys=True)) == [("entity:water", "method:eo", "relation:measures"),
                                                ("entity:water", "method:eo", "relation:uses")]


def test_missing_references_never_create_scientific_records():
    relation = Relation(**record("relation:missing", subject_id="entity:missing", predicate="uses", object_id="method:missing"))
    assert list(build_graph([relation]).nodes) == [relation.id]
