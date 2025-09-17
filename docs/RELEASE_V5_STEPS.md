# Release v5.0.0 Steps

## 1. Pré-Checklist

- CI verde (workflow darwin-integration)
- README, CHANGELOG, CITATION, zenodo.json atualizados
- repo_lint PASS (`reports/lint_qa_v5.json` ou similar)

## 2. Squash Merge

```bash
git checkout main
git pull origin main
git checkout feat/darwin-ragpp-platform
git fetch origin
# Via UI GitHub: Squash and Merge PR "Darwin RAG++ platform (v5.0)"
```

## 3. Tag & Release

Após merge em `main`:

```bash
git checkout main
git pull origin main
git tag -a v5.0.0 -m "Release v5.0.0 Darwin RAG++ Platform"
git push origin v5.0.0
```
 
Criar Release no GitHub anexando:

- `reports/qgates_report_v5.json`
- `reports/lint_qa_v5.json`
- Qualquer gráfico/figura relevante

## 4. Zenodo DOI

- GitHub Release dispara Zenodo
- Aguardar DOI de versão ser mintado
- Atualizar `CITATION.cff` (campo preferred-citation doi) e `config/metadata.yaml` version_doi

```bash
# Exemplo após obter DOI real (substituir PLACEHOLDER)
sed -i 's/10.5281\/zenodo.16921951/NEW_VERSION_DOI/g' CITATION.cff
# Ajustar version_doi
sed -i 's/version_doi: "TBD-after-zenodo-mint"/version_doi: "NEW_VERSION_DOI"/' config/metadata.yaml
git add CITATION.cff config/metadata.yaml
git commit -m "chore: update version DOI for v5.0.0"
git push origin main
```

## 5. Branch Cleanup

Listar branches:

```bash
git branch -r --sort=-committerdate
```
Para cada branch já mergeada:

```bash
LAST_SHA=$(git rev-parse origin/OLD_BRANCH)
git tag -a archive/OLD_BRANCH-$(date +%Y%m%d) -m "Archive OLD_BRANCH before deletion" $LAST_SHA
git push origin tag archive/OLD_BRANCH-$(date +%Y%m%d)
git push origin --delete OLD_BRANCH
```
 
Criar branch `next`:

```bash
git checkout main
git pull
git checkout -b next
git push origin next
```
 
Configurar proteções (via UI):

- main & next: require PR, status checks, opção linear history (se desejado)

## 6. Verificação Final Q-Gates
Confirmar tabela (README ou logs) está atualizada. Caso gates futuros pendentes, abrir issues.

## 7. Pós-Release
 
- Atualizar roadmap (README)
- Criar issues para itens de roadmap 5.0->5.1

---
Release v5.0.0 procedural guide.
