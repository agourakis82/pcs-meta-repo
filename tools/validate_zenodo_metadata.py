#!/usr/bin/env python3
"""
Valida metadados Zenodo para conformidade com Zenodo RDM.
Verifica ORCID, upload_type, creators, etc.
"""
import json
import os
import re
import sys
from pathlib import Path

ORCID_PATTERN = re.compile(r'^(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$')

def validate_orcid(orcid):
    """Valida ORCID: deve ser numérico, não começar com 0009-, não ser URL."""
    if not orcid:
        return True  # OK se ausente
    if isinstance(orcid, str):
        if orcid.startswith('https://'):
            return False  # Deve ser numérico
        if orcid.startswith('0009-'):
            return False
        return bool(ORCID_PATTERN.match(orcid))
    return False

def validate_zenodo_json(file_path):
    """Valida .zenodo.json."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if data.get('upload_type') != 'software':
            errors.append("upload_type deve ser 'software'")

        creators = data.get('creators', [])
        if not creators:
            errors.append("creators não pode estar vazio")
        for i, creator in enumerate(creators):
            name = creator.get('name')
            if not name:
                errors.append(f"creator[{i}]: name ausente")
            orcid = creator.get('orcid')
            if orcid and not validate_orcid(orcid):
                errors.append(f"creator[{i}]: ORCID inválido '{orcid}'")

        license_ = data.get('license')
        if license_ and license_ not in ['MIT', 'cc-by-4.0', 'other-open']:  # Exemplo
            errors.append(f"license '{license_}' pode ser inválido")

        related = data.get('related_identifiers', [])
        for rel in related:
            if rel.get('scheme') != 'doi':
                continue
            doi = rel.get('identifier')
            if doi and not doi.startswith('10.5281/zenodo.'):
                errors.append(f"related_identifier DOI '{doi}' não é Zenodo")

    except Exception as e:
        errors.append(f"Erro ao ler/parsing {file_path}: {e}")

    return errors

def validate_citation_cff(file_path):
    """Valida CITATION.cff."""
    errors = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        for line_no, line in enumerate(lines, 1):
            if line.strip().startswith('orcid:'):
                orcid_value = line.split(':', 1)[1].strip().strip('"')
                if orcid_value and not validate_orcid(orcid_value):
                    errors.append(f"Linha {line_no}: ORCID inválido '{orcid_value}'")

    except Exception as e:
        errors.append(f"Erro ao ler {file_path}: {e}")

    return errors

def main():
    root_dir = Path(__file__).parent.parent
    zenodo_file = root_dir / '.zenodo.json'
    citation_file = root_dir / 'CITATION.cff'
    zenodo_release = root_dir / '.zenodo.release.json'
    citation_release = root_dir / 'CITATION.release.cff'

    all_errors = []

    # Validar arquivos release se existirem, senão os fonte
    if zenodo_release.exists():
        all_errors.extend(validate_zenodo_json(zenodo_release))
    elif zenodo_file.exists():
        all_errors.extend(validate_zenodo_json(zenodo_file))

    if citation_release.exists():
        all_errors.extend(validate_citation_cff(citation_release))
    elif citation_file.exists():
        all_errors.extend(validate_citation_cff(citation_file))

    # Log
    log = {
        'valid': len(all_errors) == 0,
        'errors': all_errors
    }
    reports_dir = root_dir / 'reports'
    reports_dir.mkdir(exist_ok=True)
    with open(reports_dir / 'zenodo_validate.json', 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

    if all_errors:
        print("Erros de validação:")
        for err in all_errors:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("Validação OK.")

if __name__ == '__main__':
    main()
