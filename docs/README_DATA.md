# Data Fetch Pack — PCS Symbolic First (SWOW & ZuCo)

This pack helps you fetch **public datasets** and place them under the canonical layout:

```
data/
  raw_public/
    swow/en/          # SWOW-EN CSVs
    swow/es/          # SWOW-ES (optional)
    zuco/v1/          # ZuCo 1.0
    zuco/v2/          # ZuCo 2.0
  processed/          # derivatives created by notebooks
```

## Quick Start

1) Create a Python env and install `osfclient` (for OSF downloads):
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip osfclient
```

2) (Optional) Set OSF token (to avoid rate limits):
- Create a token at https://osf.io/settings/tokens/
- Export it before running the script:
```bash
export OSF_TOKEN="paste-your-token-here"
```

3) Run the fetch script **from the repository root**:
```bash
bash scripts/fetch_data.sh
```

4) Verify checksums (generates `provenance.yaml` with sizes & sha256):
```bash
bash scripts/compute_checksums.sh
```

## Official Sources

- **SWOW** (Small World of Words): https://smallworldofwords.org/en/project/research
- **ZuCo 1.0** (OSF project `q3zws`): https://osf.io/q3zws/
- **ZuCo 2.0** (OSF project `2urht`): https://osf.io/2urht/

> SWOW provides CSVs per language. Download EN/ES manually or add direct CSV URLs to the script section "SWOW (optional curl)". ZuCo folders are cloned via `osfclient` to preserve structure.
