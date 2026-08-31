# Deep Research Synthesis — Semillero Scientific Knowledge Brain

Generated: 2026-08-30

## Scope
This source bundle consolidates the deep-research findings around a local-first scientific knowledge brain for Earth Observation, with three epistemologically distinct pilot lines: **surface-water observation/detection**, **groundwater-potential mapping**, and **geothermal prospectivity**. It also covers the most actionable 2024–2026 implementation frontier: EO foundation models, multimodal learning, physics-informed inverse modeling, and reproducible local knowledge-graph infrastructure.

## Most consequential findings

### 1. Surface water is the cleanest first experimental line
Surface water can be observed directly from Earth-observation imagery. Pekel et al. and JRC Global Surface Water provide a strong historical/benchmark anchor, while Landsat, Sentinel-2 and HLS provide reproducible data pipelines. This makes surface-water segmentation/change detection an excellent first implementation benchmark before tackling subsurface inference.

### 2. Groundwater potential is *not* direct satellite detection
The groundwater reviews make validation the central scientific issue. EO/GIS variables are proxies or conditioning factors; credible GPM work should be validated with field information reflecting aquifer productivity (well yield, discharge, transmissivity, specific capacity, etc.). The 2026 review points to XAI, uncertainty, multisource integration and transferability as research opportunities.

### 3. PINNs are scientifically meaningful when tied to governing physics
The KLE-PINN groundwater inverse-modeling paper is a key bridge between AI and hydrogeology: use physical equations and observations to infer fields such as hydraulic conductivity. This is stronger scientifically than treating satellite pixels as direct groundwater labels. A longer-term research path is EO/GIS priors + hydrogeologic observations + physics-informed inverse models/neural operators.

### 4. Geothermal EO is an evidence-fusion problem
The geothermal literature consistently treats SWIR alteration, TIR/LST anomalies, lineaments/structures, InSAR deformation, hot springs/fumaroles and geophysical/geochemical data as evidence layers. Surface proxies must not be promoted to confirmed reservoir existence. Recent reviews emphasize hybrid expert/statistical/ensemble ML, explainability and uncertainty.

### 5. EO foundation models are already implementable, not just conceptual
Prithvi-EO-2.0, TerraMind, Clay, DOFA, SatMAE, TerraTorch and TorchGeo make it practical to compare classical task-specific baselines against pretrained geospatial models. TerraMind is especially interesting for multimodal optical+SAR hypotheses; Prithvi-EO-2.0 is especially attractive for HLS/time-series work.

## Research clusters for the future graph

1. **Foundations** — remote sensing, spectral physics, GIS, image processing, probability/statistics, optimization, PDEs, fluid flow, heat transfer, geology, hydrogeology, geophysics.
2. **Surface water** — Landsat/Sentinel/HLS → indices/segmentation/change detection → JRC GSW → temporal/generalization experiments.
3. **Groundwater** — geomorphology/geology/lineaments/rainfall/soil/topography → GPM → field validation → uncertainty/XAI/transferability → PINN inverse modeling.
4. **Geothermal** — SWIR alteration + TIR/LST + structures + InSAR + geophysics/geochemistry → prospectivity → validation/uncertainty → reservoir/techno-economic linkage.
5. **EO foundation models** — SatMAE → Prithvi/DOFA/Clay/TerraMind → TerraTorch/TorchGeo → downstream benchmarks.
6. **Scientific KB infrastructure** — Pydantic/YAML canonical records → NetworkX MultiDiGraph → SQLite FTS5 search → PyVis HTML view → provenance traversal.

## High-value research directions

- Multimodal EO foundation models (optical + SAR + temporal context) for surface-water/flood segmentation and geographic generalization.
- Groundwater potential mapping focused on field validation, uncertainty quantification, XAI and transfer across regions rather than another isolated classifier comparison.
- EO/geology/geophysics + physics-informed inverse modeling for groundwater or hydrothermal systems.
- Geothermal prospectivity with explicit evidence provenance, uncertainty and hybrid expert/data-driven modeling.
- Knowledge-graph-assisted literature synthesis where every scientific relation can traverse back to Evidence and Source.

## Epistemic firewall

- `surface_water_observation` ≠ `groundwater_presence`
- `groundwater_potential` = indirect inference requiring validation
- `thermal_anomaly / alteration / lineament` ≠ `confirmed_geothermal_reservoir`
- `LLM inference` ≠ `verified fact`
- confidence ≠ verification status

## Recommended use in SDD
Treat this archive as **source context**, not as automatically approved scientific truth. Import the catalog and graph as candidate/human-seed material. During APPLY, local PDFs supplied by the researcher should be registered, evidence should use exact locators, and claims should only be promoted according to the approved curation workflow.
