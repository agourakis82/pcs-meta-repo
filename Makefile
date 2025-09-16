SHELL := bash
.PHONY: init checksum validate linkcheck package freeze \
	fetch-geco fetch-derco fetch-onestop fetch-lpp fetch-all \
	ingest-geco ingest-derco ingest-onestop ingest-lpp \
	provenance-fill qa-external external-datasets-all \
	qa tidy-rt tidy-eeg kec integrate models figs all

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

# ==========================
# External datasets pipeline
# ==========================

fetch-geco:
	@python scripts/fetch_external.py --dataset geco

fetch-derco:
	@python scripts/fetch_external.py --dataset derco

fetch-onestop:
	@python scripts/fetch_external.py --dataset onestop

fetch-lpp:
	@python scripts/fetch_external.py --dataset lpp

fetch-all:
	@python scripts/fetch_external.py --dataset all

ingest-geco:
	@echo "[ingest-geco] RUN_MODE=full STRICT=1"
	@RUN_MODE=full STRICT=1 python -c "import sys; sys.path[:0]=['.','src']; from datasets.geco_loader import run; p=run(); print(p)"

ingest-derco:
	@echo "[ingest-derco] RUN_MODE=full STRICT=1"
	@RUN_MODE=full STRICT=1 python -c "import sys; sys.path[:0]=['.','src']; from datasets.derco_eeg_loader import run; p=run(); print(p)"

ingest-onestop:
	@echo "[ingest-onestop] RUN_MODE=full STRICT=1"
	@RUN_MODE=full STRICT=1 python -c "import sys; sys.path[:0]=['.','src']; from datasets.onestop_loader import run; p=run(); print(p)"

ingest-lpp:
	@echo "[ingest-lpp] RUN_MODE=full STRICT=1"
	@RUN_MODE=full STRICT=1 python -c "import sys; sys.path[:0]=['.','src']; from datasets.lpp_eeg_loader import run; p=run(); print(p)"

provenance-fill:
	@python -m scripts.fill_provenance

qa-external:
	@STRICT=1 python -m scripts.qa_external

external-datasets-all:
	@echo "🚀 DX-CODEX External Datasets Complete Pipeline" 
	@echo "==============================================" 
	@echo "1️⃣ Downloading external datasets..." 
	@$(MAKE) fetch-all 
	@echo "" 
	@echo "2️⃣ Processing datasets to harmonised format..." 
	@$(MAKE) ingest-geco || true
	@$(MAKE) ingest-onestop || true
	@$(MAKE) ingest-derco || true
	@$(MAKE) ingest-lpp || true
	@echo "" 
	@echo "3️⃣ Generating provenance and quality reports..." 
	@$(MAKE) provenance-fill 
	@$(MAKE) qa-external || true

# ==========================
# Diagrams (Graphviz)
# ==========================

.PHONY: fig-architecture
fig-architecture:
	@mkdir -p figures
	@which dot >/dev/null 2>&1 || { echo "[make] ERROR: graphviz 'dot' not found. Install with 'conda install -c conda-forge graphviz' or 'apt-get install graphviz'."; exit 1; }
	@dot -Tpng docs/architecture.dot -o figures/architecture.png && echo "[make] generated figures/architecture.png"

# ==========================
# GUI Build & Install
# ==========================

.PHONY: gui-install gui-uninstall gui-run gui-run-demo gui-run-full gui-build gui

gui-build:
	@echo "[make] Building PCS AI Research Suite GUI..."
	@./build_install.sh install

gui-install: gui-build
	@echo "[make] GUI installation complete"

gui-uninstall:
	@echo "[make] Uninstalling PCS AI Research Suite GUI..."
	@./build_install.sh uninstall

gui:
	@echo "[make] Launching PCS AI Research Suite..."
	@./pcs

gui-run:
	@echo "[make] Launching PCS AI Research Suite (Clean)..."
	@python3 scripts/pcs_clean_gui.py

gui-run-demo:
	@echo "[make] Launching PCS AI Research Suite (Demo)..."
	@python3 scripts/pcs_demo_gui.py

gui-run-full:
	@echo "[make] Launching PCS AI Research Suite (Full)..."
	@python3 scripts/pcs_gui.py

# Additional targets for v4.4

qa:
	ruff check . && ruff format --check .
	python tools/repo_lint.py
	python -m scripts.compute_checksums --inventory repo
	bash tools/verify_v4.4_structure.sh || true

tidy-rt:
	python -m scripts.swow_zuco_pipeline --step tidy_rt --datasets zuco_rt,geco_et,onestop_et

tidy-eeg:
	python -m scripts.swow_zuco_pipeline --step tidy_eeg --datasets zuco_eeg,derco_eeg,lpp_eeg

kec:
	python -m src.cli.kec_compile --lang en,es,nl,zh --step all --device auto --resume

integrate:
	python -m scripts.swow_zuco_pipeline --step integrate

models:
	python scripts/swow_zuco_pipeline.py --step models_rt
	python scripts/swow_zuco_pipeline.py --step models_eeg
	Rscript scripts/r_mixedlm_check.R || true

figs:
	python -m src.figures.make_figures --version v4.4

all: qa tidy-rt tidy-eeg kec integrate models figs qa
