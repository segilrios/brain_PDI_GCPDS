"""Rebuildable local search and exports derived from canonical records."""
import json
import re
import sqlite3
from collections.abc import Iterable
from pathlib import Path

from .graph import build_graph
from .models import Record, Source
from .yaml_records import dump_yaml


def _ordered(records: Iterable[Record]) -> list[Record]:
    return sorted(records, key=lambda record: record.id)


def _text(record: Record) -> tuple[str, str, str]:
    return (
        getattr(record, "title", getattr(record, "statement", getattr(record, "label", ""))),
        " ".join(getattr(record, "domains", [])),
        str(getattr(record, "source_role", type(record).__name__)),
    )


def build_index(records: Iterable[Record], path: str | Path) -> None:
    """Replace a local FTS5 derivative with a stable canonical-record index."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.unlink()
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE VIRTUAL TABLE records USING fts5(id UNINDEXED, text, domains, role, lifecycle UNINDEXED)")
        connection.executemany(
            "INSERT INTO records VALUES (?, ?, ?, ?, ?)",
            [(record.id, *_text(record), record.lifecycle.value) for record in _ordered(records)],
        )
        connection.commit()
    finally:
        connection.close()


def query_index(path: str | Path, query: str, limit: int = 20) -> list[str]:
    """Return bounded IDs; tokenize input so FTS operators never reach MATCH."""
    terms = [term for term in re.findall(r"[\w]+", query, flags=re.UNICODE) if term.lower() not in {"and", "or", "not", "near"}]
    if not terms:
        return []
    expression = " ".join(f'"{term}"' for term in terms)
    connection = sqlite3.connect(path)
    try:
        rows = connection.execute(
            "SELECT id FROM records WHERE records MATCH ? ORDER BY id LIMIT ?",
            (expression, max(1, min(limit, 100))),
        )
        return [row[0] for row in rows]
    finally:
        connection.close()


def graph_json(records: Iterable[Record]) -> str:
    """Serialize the derived graph with sorted IDs and relation keys."""
    graph = build_graph(_ordered(records))
    payload = {
        "edges": [{"source": source, "target": target, "id": key, "kind": kind}
                  for source, target, key, kind in sorted(graph.edges(keys=True, data="kind"))],
        "nodes": [{"id": identifier, "type": data["record_type"], "lifecycle": data["lifecycle"]}
                  for identifier, data in sorted(graph.nodes(data=True))],
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def csl_json(records: Iterable[Record]) -> str:
    """Generate CSL-JSON directly from Source records, never a second registry."""
    entries = []
    for source in (record for record in _ordered(records) if isinstance(record, Source)):
        entry = {"id": source.id, "type": source.publication_type, "title": source.title,
                 "author": [{"literal": author.name} for author in source.authors],
                 "issued": {"date-parts": [[source.year]]}, "container-title": source.venue}
        if source.doi:
            entry["DOI"] = source.doi
        if source.url:
            entry["URL"] = source.url
        entries.append(entry)
    return json.dumps(entries, sort_keys=True, separators=(",", ":"))


def canonical_yaml(records: Iterable[Record]) -> dict[str, str]:
    """Reuse canonical YAML serialization without modifying its records."""
    return {record.id: dump_yaml(record) for record in _ordered(records)}
