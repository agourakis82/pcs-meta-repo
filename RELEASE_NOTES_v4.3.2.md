# Release Notes — v4.3.2

Summary
- Patch release delivering data crystallization (L0→L1→L2), provenance, and reproducibility scaffolding.
- No changes to scientific outcomes; editorial/curatorial improvements only.

Motivation
- Standardize data layout and enforce contracts to ensure repeatable processing.
- Provide transparent provenance and checksums for integrity verification.

Methods (IMRaD)
- Introduction: Clarify data layers (L0 raw, L1 tidy, L2 derived) and contractual expectations.
- Methods: Add validation scripts (pandas+PyYAML), checksum automation, and link checking.
- Results: Generated checksums.csv, validation_report.json (with SKIPPED where sources absent), linkcheck_report.json, and packaged data_release.tar.gz.
- Discussion: Enhances reproducibility and reduces integration friction across datasets.

Limitations and Biases
- Validation is contingent on availability of public L0/L1 data; missing inputs are marked SKIPPED.
- Contracts capture core schema and basic ranges; domain-specific nuances may need future refinement.

Impact
- Improves dataset/toolbox reliability and onboarding for downstream users.

Next Steps
- Upload package to Zenodo, mint Version DOI, and update CFF/metadata.
- Expand contracts (typing, enums), add automated schema tests in CI.
- Add data loaders and seeds where applicable.
