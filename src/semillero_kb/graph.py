"""Deterministic, derived provenance graph over canonical typed records."""
from collections.abc import Iterable

import networkx as nx

from .models import Claim, Evidence, Experiment, Record, Relation, Result


def _edge(graph: nx.MultiDiGraph, source: str, target: str, key: str, kind: str) -> None:
    if graph.has_node(source) and graph.has_node(target):
        graph.add_edge(source, target, key=key, kind=kind)


def build_graph(records: Iterable[Record]) -> nx.MultiDiGraph:
    """Build a stable graph using only explicit record references."""
    graph = nx.MultiDiGraph()
    ordered = sorted(records, key=lambda record: record.id)
    identifiers = {record.id for record in ordered}
    for record in ordered:
        graph.add_node(record.id, record_type=type(record).__name__, provenance=record.provenance,
                       lifecycle=record.lifecycle.value, record=record)
    evidence_by_source: dict[str, list[Evidence]] = {}
    for record in ordered:
        if record.provenance in identifiers:
            _edge(graph, record.provenance, record.id, f"provenance:{record.id}", "provenance")
        if isinstance(record, Evidence):
            parent = record.source_id or record.result_id
            _edge(graph, parent, record.id, f"evidence:{record.id}", "evidence")
            if record.source_id:
                evidence_by_source.setdefault(record.source_id, []).append(record)
        elif isinstance(record, Claim):
            _edge(graph, record.source_id, record.id, f"claim:{record.id}", "claim")
            for evidence in sorted(evidence_by_source.get(record.source_id, []), key=lambda item: item.id):
                _edge(graph, evidence.id, record.id, f"evidence-claim:{evidence.id}:{record.id}", "evidence_claim")
        elif isinstance(record, Relation):
            _edge(graph, record.subject_id, record.object_id, record.id, record.predicate)
        elif isinstance(record, Experiment):
            for input_id in sorted(record.input_ids):
                _edge(graph, input_id, record.id, f"input:{input_id}:{record.id}", "experiment_input")
        elif isinstance(record, Result):
            _edge(graph, record.experiment_id, record.id, f"result:{record.id}", "experiment_result")
    return graph


def neighbors(graph: nx.MultiDiGraph, identifier: str, direction: str = "out") -> list[str]:
    """Return unique adjacent IDs in deterministic order."""
    adjacent = graph.successors(identifier) if direction == "out" else graph.predecessors(identifier)
    if direction == "both":
        adjacent = (*graph.successors(identifier), *graph.predecessors(identifier))
    if direction not in {"out", "in", "both"}:
        raise ValueError("direction must be out, in, or both")
    return sorted(set(adjacent))


def provenance(graph: nx.MultiDiGraph, identifier: str, reverse: bool = False) -> list[str]:
    """Traverse explicit provenance edges in either direction."""
    view = graph.reverse(copy=False) if reverse else graph
    seen, pending = {identifier}, [identifier]
    while pending:
        current = pending.pop(0)
        next_ids = sorted(target for _, target, data in view.out_edges(current, data=True)
                          if data["kind"] in {"provenance", "evidence", "claim", "evidence_claim", "experiment_input", "experiment_result"})
        for next_id in next_ids:
            if next_id not in seen:
                seen.add(next_id); pending.append(next_id)
    return sorted(seen - {identifier})


def contradictions(graph: nx.MultiDiGraph) -> list[str]:
    return sorted(identifier for identifier, data in graph.nodes(data=True)
                  if getattr(data["record"], "verification_status", None) == "contradicted")


def selected_subgraph(graph: nx.MultiDiGraph, identifiers: Iterable[str]) -> nx.MultiDiGraph:
    """Return a deterministic copy containing only explicitly selected nodes."""
    return graph.subgraph(sorted(set(identifiers))).copy()
