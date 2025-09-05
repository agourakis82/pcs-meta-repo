#!/usr/bin/env python3
"""
Sanitiza metadados Zenodo para release, garantindo ORCID válidos e formato correto.
Gera .zenodo.release.json e CITATION.release.cff normalizados.
"""
import json
import os
import re
import shutil
from pathlib import Path

# Regex para ORCID válido (sem URL)
ORCID_PATTERN = re.compile(r'^(\d{4}-\d{4}-\d{4}-\d{3}[\dX])$')

def extract_orcid_from_url(url):
    """Extrai ORCID numérico de URL."""
    if url and 'orcid.org/' in url:
        match = ORCID_PATTERN.search(url)
        return match.group(1) if match else None
    return None

def sanitize_orcid(orcid):
    """Sanitiza ORCID: converte URL para numérico, remove se inválido ou começa com 0009-."""
    if not orcid:
        return None
    if orcid.startswith('https://orcid.org/'):
        orcid = extract_orcid_from_url(orcid)
    if orcid and orcid.startswith('0009-'):
        return None  # Remove ORCID inválido para Zenodo
    if orcid and ORCID_PATTERN.match(orcid):
        return orcid
    return None

def sanitize_zenodo_json(input_file, output_file):
    """Sanitiza .zenodo.json para formato release."""
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    creators = data.get('creators', [])
    for creator in creators:
        orcid = creator.get('orcid')
        sanitized = sanitize_orcid(orcid)
        if sanitized:
            creator['orcid'] = sanitized
        else:
            creator.pop('orcid', None)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def sanitize_citation_cff(input_file, output_file):
    """Sanitiza CITATION.cff para formato release."""
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Substituir orcid URLs por numéricos ou remover se inválidos
    lines = content.split('\n')
    sanitized_lines = []
    for line in lines:
        if line.strip().startswith('orcid:'):
            orcid_value = line.split(':', 1)[1].strip().strip('"')
            sanitized = sanitize_orcid(orcid_value)
            if sanitized:
                sanitized_lines.append(f'    orcid: "{sanitized}"')
            # Se inválido, omitir a linha
        else:
            sanitized_lines.append(line)

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(sanitized_lines))

def main():
    root_dir = Path(__file__).parent.parent
    zenodo_file = root_dir / '.zenodo.json'
    citation_file = root_dir / 'CITATION.cff'
    zenodo_release = root_dir / '.zenodo.release.json'
    citation_release = root_dir / 'CITATION.release.cff'

    if zenodo_file.exists():
        sanitize_zenodo_json(zenodo_file, zenodo_release)
        print(f"Sanitized .zenodo.json -> {zenodo_release}")

    if citation_file.exists():
        sanitize_citation_cff(citation_file, citation_release)
        print(f"Sanitized CITATION.cff -> {citation_release}")

    # Log
    log = {
        'sanitized_files': [str(f) for f in [zenodo_release, citation_release] if f.exists()],
        'removed_orcids': []  # Poderia rastrear, mas simplificado
    }
    reports_dir = root_dir / 'reports'
    reports_dir.mkdir(exist_ok=True)
    with open(reports_dir / 'zenodo_sanitize_log.json', 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2)

if __name__ == '__main__':
    main()
