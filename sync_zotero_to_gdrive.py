import os
import shutil
from pathlib import Path

# Caminhos adaptados ao seu Mac e Drive sincronizado
ZOTERO_STORAGE = Path.home() / "Zotero" / "storage"

# Caminho real fornecido por você:
ZOTERO_BIB = Path("/Users/demetriosagourakis/Library/CloudStorage/GoogleDrive-demetrios@agourakis.med.br/Meu Drive/soc_fractal/literature/zotero/zotero.bib")

# Pasta de destino (sincronizada com o Drive também)
GOOGLE_DRIVE_TARGET = Path("/Users/demetriosagourakis/Library/CloudStorage/GoogleDrive-demetrios@agourakis.med.br/Meu Drive/soc_fractal/refs")

# Criar pasta destino se não existir
(GOOGLE_DRIVE_TARGET / "pdfs").mkdir(parents=True, exist_ok=True)

# Copiar PDFs do Zotero para a pasta no Drive
copiados = 0
for subdir in ZOTERO_STORAGE.iterdir():
    if subdir.is_dir():
        for file in subdir.glob("*.pdf"):
            dest = GOOGLE_DRIVE_TARGET / "pdfs" / f"{subdir.name}_{file.name}"
            shutil.copy(file, dest)
            copiados += 1

# Copiar arquivo .bib exportado pelo Zotero
if ZOTERO_BIB.exists():
    dest_bib = GOOGLE_DRIVE_TARGET / "zotero.bib"
    shutil.copy(ZOTERO_BIB, dest_bib)
    print(f"✅ Arquivo .bib copiado para: {dest_bib}")
else:
    print("⚠️ Arquivo zotero.bib não encontrado.")

print(f"✅ {copiados} PDFs copiados para: {GOOGLE_DRIVE_TARGET / 'pdfs'}")