# Installation & Bootstrap (Symbolic First)

## 1) Create a branch and copy files
```bash
git checkout -b plan/symbolic-first-setup
unzip symbolic_first_pack_<TIMESTAMP>.zip -d .
git add docs/ reports/ prompts/ tools/ marketing/ manuscripts/ notebooks/ requirements.txt
git commit -m "chore: add Symbolic First starter pack"
```

## 2) Create environment (venv or conda)
```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U pip && pip install -r requirements.txt
```

## 3) Open VS Code and start
- Open `notebooks/01_swow_loader.ipynb`
- Ensure raw data under `data/raw_public/swow/` and `data/raw_public/zuco/`
- Run cells and produce outputs into `/data/processed` and `/figures`

## 4) Quality checks
- Ensure linkcheck=0; maintain seeds/pins/provenance files.
