SHELL := bash
.PHONY: init checksum validate linkcheck package freeze

init:
	@mkdir -p data/L0_raw data/L1_tidy data/L2_derived data/LICENSES data/CONTRACTS data/CHECKS scripts
	@echo "[make] init complete"

checksum:
	@if [ -f scripts/compute_checksums.py ]; then python3 scripts/compute_checksums.py; else echo "[make] INFO: scripts/compute_checksums.py not found; skipping"; fi

validate:
	@if [ -f scripts/validate_contracts.py ]; then python3 scripts/validate_contracts.py; else echo "[make] INFO: scripts/validate_contracts.py not found; skipping"; fi

linkcheck:
	@if [ -f scripts/linkcheck_local.py ]; then python3 scripts/linkcheck_local.py; else echo "[make] INFO: scripts/linkcheck_local.py not found; skipping"; fi

package:
	@echo "[make] packaging data_release.tar.gz (excluding data/L0_raw)"
	@tar --exclude-vcs --exclude='data/L0_raw' -czf data_release.tar.gz \
		data/L1_tidy data/L2_derived data/CHECKS \
		PROVENANCE.yaml DATA_DICTIONARY.md \
		CHANGELOG_v4.3.2.md RELEASE_NOTES_v4.3.2.md \
		CITATION_v4.3.2.cff metadata_v4.3.2.yaml zenodo_v4.3.2.json \
		QUALITY_GATES.md Makefile .gitattributes \
		scripts/*.py 2>/dev/null || echo "[make] WARN: some files missing; packaged what was available"
	@echo "[make] packaged data_release.tar.gz"

freeze: checksum validate linkcheck package
