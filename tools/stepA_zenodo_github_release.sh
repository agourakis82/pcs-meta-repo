#!/usr/bin/env bash
set -euo pipefail

echo "[stepA] GitHub↔Zenodo — v4.3.2 at $(date)"

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$ROOT_DIR"

# --- Config fixas do projeto ---
CONCEPT_DOI="10.5281/zenodo.16533374"
TAG="v4.3.2"
TITLE="v4.3.2 — data crystallization patch"
NOTES_FILE="RELEASE_NOTES_v4.3.2.md"
ASSET="data_release.tar.gz"
CITATION="CITATION_v4.3.2.cff"
META="metadata_v4.3.2.yaml"

# --- Sanity checks ---
if ! command -v gh >/dev/null 2>&1; then
  echo "[stepA] ERRO: GitHub CLI 'gh' não encontrado. Instale e rode 'gh auth login'." >&2
  exit 1
fi
if ! gh auth status -h github.com >/dev/null 2>&1; then
  echo "[stepA] ERRO: 'gh' não autenticado. Rode: gh auth login" >&2
  exit 1
fi
if [ ! -f "$ASSET" ]; then
  echo "[stepA] ERRO: Arquivo $ASSET não encontrado. Gere-o antes (make/package)." >&2
  exit 1
fi
if [ ! -f "$NOTES_FILE" ]; then
  echo "[stepA] ERRO: $NOTES_FILE não encontrado." >&2
  exit 1
fi

# --- Descobrir repositório (owner/repo) ---
REMOTE_URL="$(git remote get-url origin 2>/dev/null || echo "")"
if [[ "$REMOTE_URL" =~ github.com[:/]+([^/]+)/([^/.]+) ]]; then
  OWNER="${BASH_REMATCH[1]}"
  REPO="${BASH_REMATCH[2]}"
  REPO_SLUG="$OWNER/$REPO"
else
  echo "[stepA] ERRO: Não consegui deduzir owner/repo do 'origin'."
  exit 1
fi
echo "[stepA] Repo: $REPO_SLUG"

# --- Garantir tag local (se precisar) ---
if ! git tag -l | grep -q "^${TAG}$"; then
  git tag -a "$TAG" -m "$TAG" || true
fi

# --- Criar/atualizar Release no GitHub ---
if gh release view "$TAG" >/dev/null 2>&1; then
  echo "[stepA] Release $TAG já existe — atualizando asset"
  gh release upload "$TAG" "$ASSET" --clobber
else
  echo "[stepA] Criando Release $TAG"
  gh release create "$TAG" "$ASSET" --title "$TITLE" --notes-file "$NOTES_FILE"
fi

REL_URL="$(gh release view "$TAG" --json url -q .url || echo "")"
echo "[stepA] Release URL: ${REL_URL:-<desconhecida>}"
echo "[stepA] ⚠️ Verifique se o repositório está habilitado no Zenodo (Account → GitHub)."

# --- (Opcional) Capturar o Version DOI via Zenodo API ---
# Requer: export ZENODO_TOKEN=<token>; tenta achar o registro mais recente do Concept DOI.
FOUND_DOI=""
if [ -n "${ZENODO_TOKEN:-}" ]; then
  echo "[stepA] Consultando Zenodo por Version DOI (concept=${CONCEPT_DOI})"
  # Busca registros publicados (records API). Tentativa 1: query por conceptdoi
  QUERY_URL="https://zenodo.org/api/records/?q=conceptdoi:${CONCEPT_DOI}&sort=mostrecent&size=1"
  JSON="$(curl -sS "$QUERY_URL" || true)"
  if [ -n "$JSON" ]; then
    # Extrair DOI usando Python (evita dependência em jq)
    FOUND_DOI="$(python3 - <<'PY'
import sys, json
try:
    data=json.load(sys.stdin)
    hits=data.get('hits',{}).get('hits',[])
    if hits:
        rec=hits[0]
        doi=rec.get('doi') or rec.get('metadata',{}).get('doi') or rec.get('links',{}).get('doi')
        if doi:
            print(doi.strip())
except Exception: pass
PY
<<< "$JSON")"
  fi
  if [ -n "$FOUND_DOI" ]; then
    echo "[stepA] Zenodo Version DOI: $FOUND_DOI"
  else
    echo "[stepA] INFO: DOI ainda não disponível via API (talvez integração não habilitada ou processamento em curso)."
  fi
else
  echo "[stepA] INFO: Variável ZENODO_TOKEN não definida — pulando consulta à API do Zenodo."
fi

# --- Atualizar arquivos com DOI (se encontrado) ---
if [ -n "$FOUND_DOI" ]; then
  echo "[stepA] Atualizando $CITATION e $META com o DOI encontrado"
  python3 - "$CITATION" "$META" "$FOUND_DOI" <<'PY'
import sys, re, pathlib
cit, meta, doi = sys.argv[1], sys.argv[2], sys.argv[3]
def sub_file(p, patterns):
    t = pathlib.Path(p).read_text(encoding='utf-8')
    for pat, rep in patterns:
        t2, n = re.subn(pat, rep, t, flags=re.M)
        t = t2
    pathlib.Path(p).write_text(t, encoding='utf-8')
# CITATION_v4.3.2.cff: line starting with 'doi:'
sub_file(cit, [(r'(?m)^doi:\s*""\s*$', f'doi: "{doi}"')])
# metadata_v4.3.2.yaml: line starting with 'version_doi:'
sub_file(meta, [(r'(?m)^version_doi:\s*""\s*$', f'version_doi: "{doi}"')])
print("[stepA] DOI injected into metadata files.")
PY
  git add "$CITATION" "$META" || true
  git commit -m "docs: add Zenodo Version DOI to v4.3.2" || true
else
  echo "[stepA] Skipping DOI injection (not available). Você pode editar manualmente depois."
fi

echo "[stepA] Concluído. Próximos passos:"
echo " - Se o DOI não apareceu: confirme no Zenodo se o repo GitHub está habilitado e aguarde o processamento."
echo " - Depois, atualize os badges/README se necessário."

