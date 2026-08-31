# Recommended Human Seed Corpus

These 20 resources are strong starting anchors. They are **relevance seeds, not unquestionable truth**.

1. **High-resolution mapping of global surface water and its long-term changes** (2016) — `seminal, foundational, benchmark` — Foundational global surface-water mapping reference; establishes a long temporal Landsat baseline and the JRC Global Surface Water product.
   - https://www.nature.com/articles/nature20584
2. **Analysis of methods used to validate remote sensing and GIS-based groundwater potential maps in the last two decades: A review** (2024) — `review, methodological` — Reviews 125 studies and makes validation quality a central issue; field data reflecting aquifer productivity are preferable validation evidence.
   - https://doi.org/10.1016/j.geogeo.2023.100245
3. **Groundwater Potential Mapping Using Machine Learning Techniques: Current Trends and Future Perspectives** (2026) — `review, state_of_the_art` — Recent synthesis emphasizing explainability, uncertainty, multi-source integration and transferability as research gaps.
   - https://www.mdpi.com/2073-4441/18/8/947
4. **Groundwater inverse modeling: Physics-informed neural network with disentangled constraints and errors** (2024) — `methodological, state_of_the_art` — Concrete physics-informed inverse-modeling route: estimates hydraulic conductivity using a PINN plus Karhunen–Loève expansion.
   - https://www.sciencedirect.com/science/article/pii/S0022169424010990
5. **Geologic remote sensing for geothermal exploration: A review** (2014) — `foundational, review` — Foundational review connecting SWIR alteration mineralogy, TIR temperature/heat flux and InSAR deformation with geothermal exploration.
   - https://www.sciencedirect.com/science/article/abs/pii/S0303243414001275
6. **Advances in geothermal energy prospectivity mapping research based on machine learning in the age of big data** (2023) — `review, methodological` — Maps the transition from conventional prospectivity mapping to ML-enhanced play fairway analysis.
   - https://www.sciencedirect.com/science/article/pii/S221313882300543X
7. **Review on geothermal prospectivity mapping: Global trends, challenges, and future directions** (2026) — `review, state_of_the_art` — Current global review (~100 studies); highlights hybrid expert+statistical+ensemble approaches, XAI and uncertainty as frontier issues.
   - https://www.sciencedirect.com/science/article/pii/S1364032126004636
8. **Advances in Thermal Infrared Remote Sensing Technology for Geothermal Resource Detection** (2024) — `review, methodological` — Modern TIR-focused review; stresses integration with geology, geophysics and geochemistry.
   - https://www.mdpi.com/2072-4292/16/10/1690
9. **Prithvi-EO-2.0: A Versatile Multi-Temporal Foundation Model for Earth Observation Applications** (2024) — `methodological, state_of_the_art` — Strong open EO foundation model: 300M/600M models trained on 4.2M global HLS time-series samples with temporal/location embeddings.
   - https://arxiv.org/abs/2412.02732
10. **TerraMind: Large-Scale Generative Multimodality for Earth Observation** (2025) — `methodological, state_of_the_art` — Any-to-any generative multimodal EO foundation model trained across nine modalities; introduces Thinking-in-Modalities.
   - https://arxiv.org/abs/2504.11171
11. **SatMAE: Pre-training Transformers for Temporal and Multi-Spectral Satellite Imagery** (2022) — `seminal, methodological` — Seminal EO masked-autoencoder work explicitly modeling temporal and multispectral satellite structure.
   - https://arxiv.org/abs/2207.08051
12. **Foundation Models for Remote Sensing and Earth Observation: A Survey** (2025) — `review, state_of_the_art` — Broad taxonomy and benchmark-oriented survey spanning visual, vision-language and other RS foundation models.
   - https://arxiv.org/abs/2410.16602
13. **The Harmonized Landsat and Sentinel-2 Version 2.0 Surface Reflectance Dataset** (2025) — `dataset, methodological` — Analysis-ready harmonized Landsat/Sentinel-2 dataset underpinning Prithvi-EO-2.0 and many temporal EO workflows.
   - https://hls.gsfc.nasa.gov/documents/
14. **NASA-IMPACT/Prithvi-EO-2.0** (2024) — `implementation` — Official code/examples for Prithvi-EO-2.0 fine-tuning.
   - https://github.com/NASA-IMPACT/Prithvi-EO-2.0
15. **IBM/terramind** (2025) — `implementation` — Official TerraMind code examples, generation and fine-tuning.
   - https://github.com/IBM/terramind
16. **TerraTorch** (2024) — `implementation, tooling` — Fine-tuning framework for geospatial foundation models; integrates with TorchGeo and multiple model families.
   - https://github.com/torchgeo/terratorch
17. **TorchGeo** (2025) — `implementation, tooling` — PyTorch geospatial datasets, samplers, transforms and pretrained models; strong implementation substrate.
   - https://github.com/torchgeo/torchgeo
18. **JRC Global Surface Water Mapping Layers v1.4** (2021) — `benchmark, dataset` — Global 30 m surface-water occurrence/change layers derived from 4.7M+ Landsat scenes through 2021.
   - https://developers.google.com/earth-engine/datasets/catalog/JRC_GSW1_4_GlobalSurfaceWater
19. **Harmonized Landsat and Sentinel-2 v2.0 (HLS)** (2025) — `dataset, analysis_ready_data` — Analysis-ready harmonized Landsat/Sentinel-2 surface reflectance with frequent revisit; core pretraining source for Prithvi-EO-2.0.
   - https://hls.gsfc.nasa.gov/data-access-and-tools/
20. **USGS Geothermal Data Releases** (2026) — `dataset_catalog` — Official geothermal data releases including magnetotellurics, resource favorability and geochemical/hydrologic data.
   - https://www.usgs.gov/search?f%5B0%5D=usgs_facet%3Aproducts_data&keywords=Geothermal

## Expansion policy
Use bounded backward/forward citation snowballing from these seeds. Admit new sources when they add foundational relevance, direct methodological relevance, code/data, state-of-the-art evidence, validation evidence, or contradiction/support for an existing claim. Do not recursively expand unverified candidates.
