from pathlib import Path

from semillero_kb.cli import main
from semillero_kb.models import Entity, Relation
from semillero_kb.visualization import visualization_html, write_visualization


def records():
    base = {"provenance": "fixture", "version": 1}
    water = Entity(id="entity:water", entity_type="Concept", label="Water", **base)
    method = Entity(id="method:eo", entity_type="Method", label="EO", **base)
    relation = Relation(id="relation:uses", subject_id=water.id, predicate="uses", object_id=method.id, **base)
    return [water, method, relation]


def test_visualization_is_deterministic_and_keeps_explicit_labels_and_roles(tmp_path):
    first = visualization_html(records())
    assert first == visualization_html(reversed(records()))
    assert '"label":"Water"' in first and '"role":"Entity"' in first and '"kind":"uses"' in first
    assert "Search" in first and "Filter" in first and "onwheel" in first and "Select a node" in first
    assert write_visualization(records(), tmp_path / "index.html").read_text(encoding="utf-8") == first


def test_visualize_cli_writes_requested_html(tmp_path, capsys):
    fixture = Path(__file__).parents[1] / "fixtures" / "valid_claim.yaml"
    output = tmp_path / "knowledge.html"
    assert main(["visualize", str(fixture), "--output", str(output)]) == 0
    assert output.exists() and "claim:synthetic-water" in output.read_text(encoding="utf-8")
    assert "visualization written" in capsys.readouterr().out
