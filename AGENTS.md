# Repository Operating Contract

This repository is the research home of the Semillero de Investigación en Ciencia de Datos e Inteligencia Artificial. It supports work in data science, artificial intelligence, mathematics, and related fields, including experimental software when research requires it. The project builds reusable knowledge progressively. Every contribution MUST make its purpose, evidence, uncertainty, and reproducibility clear without inventing facts, citations, results, or provenance.

## Scope and Purpose

- Treat research questions, scientific claims, methods, datasets, and analyses as first-class work products.
- Preserve knowledge so that another researcher or agent can understand, reproduce, challenge, and extend it.
- Build only the software, automation, and structure justified by an actual research need; do not introduce technology architecture speculatively.

## SDD Workflow

Use Spec-Driven Development for planned changes:

1. Explore the problem and current repository state before committing to a solution.
2. Propose the intent, scope, capabilities, non-goals, and risks.
3. Write testable specifications with explicit requirements and scenarios.
4. Design only the technical approach needed to satisfy the approved specification.
5. Break the work into small, reviewable tasks.
6. Apply only assigned tasks, preserving prior progress and recording evidence.
7. Verify implementation against the specification, design, tasks, and runtime evidence.
8. Archive completed work only after verification.

Use Engram as operational project memory for decisions, discoveries, constraints, progress, and session continuity. Engram is not formal scientific knowledge, a source of truth for research claims, or a substitute for versioned repository artifacts. Record durable scientific and software artifacts in Git.

## Research Artifacts and Integrity

- Store persistent scientific artifacts in this repository and version them with Git. This includes sources, claims, ontologies, knowledge graphs, experiments, notebooks, datasets or dataset manifests, and reports.
- Keep artifacts reviewable and record enough metadata to reproduce their origin and execution.
- Preserve source identity, acquisition or generation details, transformations, parameters, environment information, and artifact relationships where relevant.
- Every claim MUST have traceable evidence or be explicitly labeled as an assumption, interpretation, proposal, or unresolved question.
- Cite only sources that were actually consulted. Never fabricate citations, quotations, identifiers, datasets, measurements, or provenance.
- Record failed, inconclusive, and negative results when they are valid observations; do not hide them or present absence of evidence as evidence of absence.
- Experiments MUST be reproducible from documented inputs, code, parameters, and commands, subject to clearly stated external dependencies and limitations.

## Auditable Knowledge

Maintain the scientific knowledge graph separately from Engram operational memory. Model explicit entities and relations, and keep the graph distinct from raw research artifacts while linking to them. Each node and relationship MUST identify its evidence or provenance and distinguish observed facts from interpretations or inferences.

Represent uncertainty explicitly. Preserve contradictions rather than silently resolving them; record the competing claims, their evidence, and their status. Inference MAY guide investigation, but MUST NOT be stored or presented as fact without supporting evidence.

## Software Changes

- Keep Git history coherent: make small, focused, reversible changes with clear intent.
- Follow existing repository conventions and keep unrelated work out of a change.
- Add or update tests for behavior that can be tested. Run the narrowest relevant checks, then broader checks when available.
- Report commands and outcomes honestly. A skipped, unavailable, or failing check is not success.
- Do not claim completion when required evidence is missing.

## Agent Conduct

Agents MUST inspect relevant context before acting, state assumptions, and stop when requirements or evidence are insufficient. Use the smallest useful set of skills and subagents; read each selected skill's instructions before following it. Delegate broad exploration, multi-file implementation, and execution-heavy verification when the applicable orchestration rules require it. Do not delegate trivial mechanical work unnecessarily, and do not let delegation replace human approval for product or scope decisions.

Do not create scaffolding, architecture, research-system components, or artifacts outside the requested scope. Do not commit, publish, or modify unrelated files unless explicitly authorized.

## Language and Naming

Technical artifacts, identifiers, comments, and repository documentation use concise professional English by default. Preserve the language of existing artifacts when extending them unless the task specifies otherwise. Use precise domain terms; define specialized terms at first use. User-facing explanations may follow the user's language, but must not alter the language conventions of repository artifacts.

