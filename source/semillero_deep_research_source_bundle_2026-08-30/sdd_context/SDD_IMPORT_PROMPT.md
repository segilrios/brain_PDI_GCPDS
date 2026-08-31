# SDD Import Prompt

Use this archive as external research-source context for the existing SDD change `local-first-research-knowledge-base`.

1. Do not treat catalog entries or model-generated synthesis as automatically verified facts.
2. Preserve source IDs and URLs/DOIs.
3. Import the recommended seed corpus as candidate/human-seed material pending human curation.
4. Preserve the epistemic firewall: surface water ≠ groundwater potential ≠ geothermal reservoir confirmation.
5. Use `research/knowledge/edges.jsonl` only as candidate graph structure; scientific relations must retain Claim/Evidence provenance when promoted into the canonical KB.
6. Do not download or commit publisher PDFs automatically.
7. Use repository/dataset links for implementation planning and reproducibility.
8. During APPLY, ingest researcher-provided local PDFs with exact page/section locators and keep PDFs outside Git.
9. Use bounded snowballing from approved seeds through OpenAlex/Crossref/Semantic Scholar or publisher citation graphs; never recursively expand unverified candidates.
10. Record all additions, exclusions and promotion decisions in the corpus expansion log required by DESIGN.
