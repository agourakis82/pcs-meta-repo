# Release Notes — v4.3.3

Summary
- Patch release to validate GitHub↔Zenodo integration and metadata.
- No changes to scientific outcomes or datasets.

Motivation
- Ensure creators (ORCID), related identifiers, and resource type are correct in Zenodo.

Methods (IMRaD)
- Introduction: Same scope as v4.3.2; integration-only patch.
- Methods: Added `.zenodo.json`, automation scripts for DOI injection and draft completion.
- Results: New GitHub release triggers a fresh Zenodo draft with clean metadata.
- Discussion: Streamlines DOI minting and release reproducibility flow.

Limitations and Biases
- Package payload unchanged from v4.3.2 (excludes L0); metadata improvements only.

Impact
- Improves reliability of citation and archiving workflows.
