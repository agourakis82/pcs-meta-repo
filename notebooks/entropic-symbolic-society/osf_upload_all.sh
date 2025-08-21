#!/usr/bin/env bash
set -euo pipefail

############################################
# CONFIGURAÇÃO — AJUSTE ESTES VALORES
############################################

# Caminho da raiz do seu repo (entre aspas; há espaços no caminho)
ROOT="/Users/demetriosagourakis/Library/Mobile Documents/com~apple~CloudDocs/Biologia Fractal/entropic-symbolic-society"

# Subprojeto NHB
NHB="$ROOT/NHB_Symbolic_Mainfold"

# Python (ambiente do projeto)
PY="$ROOT/.venv/bin/python"  # se preferir: PY="python3"

# Token do OSF (exporte no shell antes ou defina aqui — mas EVITE commitar!)
# export OSF_TOKEN="COLE_SEU_TOKEN_AQUI"

# IDs/DOIs dos componentes OSF (IDs = os 5 chars ao fim do DOI OSF)
RAW_ID="C4RDH"        # Raw_Data_SWOW — DOI 10.17605/OSF.IO/C4RDH
DERIVED_ID="CS3GN"    # Derived_Data_and_Results — DOI 10.17605/OSF.IO/CS3GN
VALIDATION_ID="WF67R" # Validation — DOI 10.17605/OSF.IO/WF67R
NEURO_ID="W2C34"      # Neuro_Integration_RSA — DOI 10.17605/OSF.IO/W2C34
PREREG_DOI="10.17605/OSF.IO/FCT5U"  # Preregistration (registro; não recebe uploads)

# Modo “ensaio” (não faz upload se DRYRUN=1)
DRYRUN="${DRYRUN:-0}"

############################################
# CHECAGENS
############################################

if [ -z "${OSF_TOKEN:-}" ]; then
  echo "❌ OSF_TOKEN não definido. Rode: export OSF_TOKEN='SEU_TOKEN_OSF'"
  exit 1
fi

# Instalar osfclient se necessário
if ! command -v osf >/dev/null 2>&1; then
  echo "ℹ️ Instalando osfclient..."
  pip install --quiet osfclient
fi

# Script de checksums/manifesto (salvar em NHB/code se ainda não existir)
CK="$NHB/code/osf_checksums_manifest.py"
if [ ! -f "$CK" ]; then
  echo "ℹ️ Criando $CK ..."
  mkdir -p "$NHB/code"
  cat > "$CK" << 'PY'
#!/usr/bin/env python3
import sys, hashlib, csv, time
from pathlib import Path

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()

def main():
    if len(sys.argv) < 2:
        print("Usage: python osf_checksums_manifest.py <target_dir> [--output <out_dir>]")
        sys.exit(1)
    target = Path(sys.argv[1]).resolve()
    out_dir = target
    if len(sys.argv) >= 4 and sys.argv[2] == "--output":
        out_dir = Path(sys.argv[3]).resolve()
        out_dir.mkdir(parents=True, exist_ok=True)

    now = time.strftime("%Y-%m-%dT%H:%M:%S")
    checksums_path = out_dir / "CHECKSUMS.sha256"
    manifest_path  = out_dir / "MANIFEST.csv"

    with checksums_path.open("w", encoding="utf-8") as chks, \
         manifest_path.open("w", newline="", encoding="utf-8") as mf:
        writer = csv.writer(mf)
        writer.writerow(["path","size","sha256","source","generated_by","created_at"])
        for p in sorted(target.rglob("*")):
            if p.is_file() and p.name not in {"CHECKSUMS.sha256", "MANIFEST.csv"}:
                h = hashlib.sha256()
                with p.open('rb') as f:
                    for chunk in iter(lambda: f.read(65536), b''):
                        h.update(chunk)
                digest = h.hexdigest()
                rel = str(p.relative_to(target))
                size = p.stat().st_size
                chks.write(f"{digest}  {rel}\n")
                writer.writerow([rel, size, digest, str(target), "osf_checksums_manifest.py", now])

    print(f"Written: {checksums_path}")
    print(f"Written: {manifest_path}")

if __name__ == "__main__":
    main()
PY
  chmod +x "$CK"
fi

############################################
# 1) CHECKSUMS / MANIFESTOS
############################################
echo "🧮 Gerando CHECKSUMS/MANIFEST para data/ e results/ ..."
if [ -d "$NHB/data" ]; then
  "$PY" "$CK" "$NHB/data" --output "$NHB/data"
else
  echo "⚠️ Pasta não encontrada: $NHB/data (pulando)"
fi
if [ -d "$NHB/results" ]; then
  "$PY" "$CK" "$NHB/results" --output "$NHB/results"
else
  echo "ℹ️ Pasta não encontrada: $NHB/results (ok, pode não existir ainda)"
fi

############################################
# 2) FUNÇÕES DE UPLOAD
############################################
upload() {
  local COMP_ID="$1"; shift
  local SRC="$1"; shift
  local DEST="$1"; shift
  if [ "$DRYRUN" = "1" ]; then
    echo "DRYRUN: osf -p ${COMP_ID} upload '${SRC}' '${DEST}' --force"
  else
    osf -p "${COMP_ID}" upload "${SRC}" "${DEST}" --force
  fi
}

upload_if_exists() {
  local COMP_ID="$1"; shift
  local SRC="$1"; shift
  local DEST="$1"; shift
  if [ -f "$SRC" ]; then
    echo "⬆️  ${SRC} → ${COMP_ID}:${DEST}"
    upload "$COMP_ID" "$SRC" "$DEST"
  else
    echo "— arquivo não encontrado (pulando): $SRC"
  fi
}

upload_glob_csv() {
  local COMP_ID="$1"; shift
  local GLOB="$1"; shift
  local DEST_DIR="$1"; shift
  shopt -s nullglob
  for f in $GLOB; do
    local base="$(basename "$f")"
    upload_if_exists "$COMP_ID" "$f" "${DEST_DIR}/${base}"
  done
  shopt -u nullglob
}

############################################
# 3) RAW DATA — C4RDH
############################################
echo "📦 RAW: $RAW_ID (10.17605/OSF.IO/C4RDH)"
# Arquivo principal e subpasta raw/
upload_if_exists "$RAW_ID" "$NHB/data/SWOW-EN.complete.20180827.csv" "raw/SWOW-EN.complete.20180827.csv"
if [ -d "$NHB/data/raw" ]; then
  upload_glob_csv "$RAW_ID" "$NHB/data/raw/*.csv" "raw"
fi
# Integridade
upload_if_exists "$RAW_ID" "$NHB/data/CHECKSUMS.sha256" "raw/CHECKSUMS.sha256"
upload_if_exists "$RAW_ID" "$NHB/data/MANIFEST.csv" "raw/MANIFEST.csv"

############################################
# 4) DERIVED — CS3GN
############################################
echo "📊 DERIVED: $DERIVED_ID (10.17605/OSF.IO/CS3GN)"
# Seleção de artefatos leves (CSV/NPY/PNG). Evitar binários pesados tipo .gpickle/.pkl aqui.
upload_if_exists "$DERIVED_ID" "$NHB/data/symbolic_cleaned_data.csv" "Derived/symbolic_cleaned_data.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/symbolic_metrics.csv" "Derived/symbolic_metrics.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/symbolic_embeddings.csv" "Derived/symbolic_embeddings.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/symbolic_metrics_embeddings.csv" "Derived/symbolic_metrics_embeddings.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/labels.csv" "Derived/labels.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/X_umap.npy" "Derived/X_umap.npy"
upload_if_exists "$DERIVED_ID" "$NHB/data/symbolic_umap_dataframe.csv" "Derived/symbolic_umap_dataframe.csv"
upload_if_exists "$DERIVED_ID" "$NHB/data/silhouette_scores.csv" "Derived/silhouette_scores.csv"
# Integridade
upload_if_exists "$DERIVED_ID" "$NHB/data/CHECKSUMS.sha256" "Derived/CHECKSUMS.sha256"
upload_if_exists "$DERIVED_ID" "$NHB/data/MANIFEST.csv" "Derived/MANIFEST.csv"

############################################
# 5) VALIDATION — WF67R
############################################
echo "🧪 VALIDATION: $VALIDATION_ID (10.17605/OSF.IO/WF67R)"
# Exemplos (ajuste conforme os nomes dos seus resultados):
upload_glob_csv "$VALIDATION_ID" "$NHB/results/*.csv" "Validation"
# Integridade (se gerada em results/)
upload_if_exists "$VALIDATION_ID" "$NHB/results/CHECKSUMS.sha256" "Validation/CHECKSUMS.sha256"
upload_if_exists "$VALIDATION_ID" "$NHB/results/MANIFEST.csv" "Validation/MANIFEST.csv"

############################################
# 6) NEURO INTEGRATION (RSA) — W2C34
############################################
echo "🧠 NEURO_RSA: $NEURO_ID (10.17605/OSF.IO/W2C34)"
# Exemplos (ajuste conforme seus nomes):
upload_if_exists "$NEURO_ID" "$NHB/results/rsa_summary_statistics.csv" "RSA/rsa_summary_statistics.csv"
upload_glob_csv "$NEURO_ID" "$NHB/results/rsa_matrices/*.csv" "RSA/rsa_matrices"

############################################
# 7) RESUMO
############################################
echo "✅ Uploads finalizados."
echo "🔗 Preregistration (registro, sem upload): $PREREG_DOI"
echo "ℹ️ Se quiser testar sem fazer upload: rode com DRYRUN=1 ./osf_upload_all.sh"
