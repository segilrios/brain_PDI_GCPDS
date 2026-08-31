"""Deterministic, self-contained graphical views of derived record graphs."""
import json
from collections.abc import Iterable
from pathlib import Path

from .graph import build_graph
from .models import Record


def _label(record: Record) -> str:
    return str(getattr(record, "label", getattr(record, "title", getattr(record, "statement", record.id))))


def visualization_html(records: Iterable[Record]) -> str:
    """Render explicit records as an offline SVG graph with client-side controls."""
    ordered = sorted(records, key=lambda record: record.id)
    graph = build_graph(ordered)
    nodes = [{"id": record.id, "label": _label(record), "type": type(record).__name__,
              "role": str(getattr(record, "source_role", type(record).__name__)),
              "lifecycle": record.lifecycle.value} for record in ordered]
    edges = [{"source": source, "target": target, "id": key, "kind": data["kind"]}
             for source, target, key, data in sorted(graph.edges(keys=True, data=True))]
    data = json.dumps({"nodes": nodes, "edges": edges}, sort_keys=True, separators=(",", ":"))
    return f"""<!doctype html>
<meta charset="utf-8"><title>Semillero knowledge graph</title>
<style>body{{font:14px sans-serif;margin:1rem}}#graph{{border:1px solid #bbb;width:100%;height:520px}}circle{{fill:#2563eb;cursor:pointer}}line{{stroke:#94a3b8}}#nodes button{{margin:2px}}</style>
<h1>Semillero knowledge graph</h1><label>Search <input id="search"></label>
<label>Filter <select id="filter"><option value="">All roles</option></select></label><button id="reset">Reset zoom</button>
<svg id="graph" viewBox="0 0 800 520" aria-label="Interactive knowledge graph"><g id="scene"></g></svg><p id="details">Select a node to navigate its metadata.</p><div id="nodes"></div>
<script>const data={data},scene=document.querySelector('#scene'),details=document.querySelector('#details'),search=document.querySelector('#search'),filter=document.querySelector('#filter'),nodes=document.querySelector('#nodes');
let zoom=1;[...new Set(data.nodes.map(n=>n.role))].sort().forEach(r=>filter.add(new Option(r,r)));
const point=(i,n)=>[400+210*Math.cos(2*Math.PI*i/n-Math.PI/2),260+210*Math.sin(2*Math.PI*i/n-Math.PI/2)];
function draw(){{const visible=data.nodes.filter(n=>!filter.value||n.role===filter.value).filter(n=>!search.value||`${{n.id}} ${{n.label}} ${{n.role}}`.toLowerCase().includes(search.value.toLowerCase()));const pos=new Map(visible.map((n,i)=>[n.id,point(i,visible.length||1)]));scene.replaceChildren();data.edges.filter(e=>pos.has(e.source)&&pos.has(e.target)).forEach(e=>{{let l=document.createElementNS('http://www.w3.org/2000/svg','line'),a=pos.get(e.source),b=pos.get(e.target);l.setAttribute('x1',a[0]);l.setAttribute('y1',a[1]);l.setAttribute('x2',b[0]);l.setAttribute('y2',b[1]);l.setAttribute('aria-label',e.kind);scene.append(l)}});visible.forEach(n=>{{let p=pos.get(n.id),c=document.createElementNS('http://www.w3.org/2000/svg','circle'),t=document.createElementNS('http://www.w3.org/2000/svg','text');c.setAttribute('cx',p[0]);c.setAttribute('cy',p[1]);c.setAttribute('r',12);c.onclick=()=>select(n);t.setAttribute('x',p[0]+16);t.setAttribute('y',p[1]+4);t.textContent=n.label;scene.append(c,t)}});nodes.replaceChildren(...visible.map(n=>{{let b=document.createElement('button');b.textContent=n.id;b.onclick=()=>select(n);return b}}));}}
function select(n){{details.textContent=`${{n.id}} — ${{n.type}} / ${{n.role}} / ${{n.lifecycle}}`;}} function transform(){{scene.setAttribute('transform',`translate(400 260) scale(${{zoom}}) translate(-400 -260)`);}} document.querySelector('#graph').onwheel=e=>{{e.preventDefault();zoom=Math.max(.5,Math.min(3,zoom+(e.deltaY<0?.1:-.1)));transform();}};document.querySelector('#reset').onclick=()=>{{zoom=1;transform();}};search.oninput=filter.onchange=draw;draw();</script>"""


def write_visualization(records: Iterable[Record], output: str | Path = "build/index.html") -> Path:
    """Write the reproducible offline visualization derivative."""
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(visualization_html(records), encoding="utf-8")
    return path
