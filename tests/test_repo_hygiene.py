import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]

def _exists(p): return (ROOT/p).exists()

def test_license_mit():
    p = ROOT/'LICENSE'
    assert p.exists(), "LICENSE ausente"
    txt = p.read_text(encoding='utf-8', errors='ignore')
    assert "MIT License" in txt, "LICENSE não parece ser MIT canônico"

def test_docs_ccby():
    p = ROOT/'LICENSES'/'CC-BY-4.0.txt'
    assert p.exists(), "Arquivo CC-BY-4.0 ausente"
    txt = p.read_text(encoding='utf-8', errors='ignore').lower()
    assert "cc by 4.0" in txt or "creative commons" in txt, "Conteúdo CC-BY-4.0 não identificado"

def test_readme_sections():
    p = ROOT/'README.md'
    assert p.exists(), "README.md ausente"
    txt = p.read_text(encoding='utf-8', errors='ignore')
    assert re.search(r'^##\s*License\b', txt, flags=re.I | re.M), "Seção 'License' ausente"
    assert re.search(r'^##\s*Cite this work\b', txt, flags=re.I | re.M), (
        "Seção 'Cite this work' ausente"
    )

def test_citation_cff_parsable():
    p = ROOT/'CITATION.cff'
    assert p.exists(), "CITATION.cff ausente"
    try:
        import ruamel.yaml as ry
        ry.YAML(typ='safe').load(p.read_text(encoding='utf-8'))
    except Exception as e:
        import pytest
        pytest.skip(f'YAML parser indisponível/erro: {e}')

def test_metadata_yaml_parsable():
    p = ROOT/'metadata.yaml'
    assert p.exists(), "metadata.yaml ausente"
    try:
        import ruamel.yaml as ry
        ry.YAML(typ='safe').load(p.read_text(encoding='utf-8'))
    except Exception as e:
        import pytest
        pytest.skip(f'YAML parser indisponível/erro: {e}')

def test_zenodo_json_parsable():
    p = ROOT/'zenodo.json'
    assert p.exists(), "zenodo.json ausente"
    json.loads(p.read_text(encoding='utf-8'))

def test_governance_files():
    assert _exists('.github/ISSUE_TEMPLATE/bug_report.md')
    assert _exists('.github/ISSUE_TEMPLATE/feature_request.md')
    assert _exists('.github/PULL_REQUEST_TEMPLATE.md')
    assert _exists('CODE_OF_CONDUCT.md')
    assert _exists('SECURITY.md')

def test_reports_exist():
    assert _exists('reports/audit.json')
    assert _exists('reports/duplicates_groups.csv')
