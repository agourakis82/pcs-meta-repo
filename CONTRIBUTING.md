# Contributing

## How to propose changes

1. Open an issue describing context, impact, evidence (English).

2. Create a feature branch and reference the issue in the PR title.

## Dev env setup

- Clone the repo and create a virtual environment.

- `pip install -r requirements.txt`

- `pre-commit install`

## Style & Lint (pre-commit)

- Run `pre-commit run --files <changed files>`

- Run tests with `pytest` when applicable.

## DCO / Signed-off-by

- All commits must use `-s/--signoff` to add a `Signed-off-by` line.

## PR checklist

- [ ] Tests added/updated

- [ ] `pre-commit` passes

- [ ] Documentation updated

- [ ] `CHANGELOG.md` updated
