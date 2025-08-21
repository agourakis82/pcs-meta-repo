# Roadmap Estratégico — Symbolic Manifolds & Entropic Dynamics (v1.4 / v1.5)

## 0) Síntese (Delta Zero)
- Programa: manifold simbólico + dinâmica entrópica + validação comportamental e neuro (EEG/fMRI).
- Estado: pacote NHB funcional (v1.5, SVD-only), documentação/DOIs, “monster review” de validação.
- Objetivo 12–24 meses: demonstrar validade preditiva clínica e alinhamento neuro (RSA), com robustez e replicação.

## 1) Onde estamos
- Raiz = guarda-chuva filosófico; dual license (MIT para código; CC BY 4.0 para texto/figuras).
- Subprojeto `NHB_Symbolic_Mainfold/` = pipeline 01–06; README técnico; CITATION.cff; requirements pinado (SVD-only).
- DOIs: Umbrella 10.5281/zenodo.16730036 | Código NHB 10.5281/zenodo.16752238 | Dados OSF 10.17605/OSF.IO/2AQP7.

## 2) Para onde vamos (12 meses)
- Mês 0–2: Paper de Métodos (NHB) + Paper Teórico (manifesto). Pré-registro de RSA (OSF).
- Mês 2–6: Validação semântica (comunidades, estabilidade) + EEG (priming/N400).
- Mês 4–9: RSA-fMRI com narrativas (≥2 datasets) + replicação cruzada.
- Mês 6–10: Robustez/Modelos nulos (transversal).
- Mês 9–12: Normativo (desvios individuais) + Clínico I (curso/risco/resposta).

## 3) Branches sugeridos (Git)
- paper-methods-nhb
- paper-theory-manifold
- paper-communities-swow
- paper-eeg-n400
- paper-rsa-fmri
- paper-robustness-nulls
- paper-normative
- paper-clinical-prediction
- paper-intervention-prepost

## 4) Critérios de sucesso (Metas mensuráveis)
- Semântica: estabilidade de clusters ≥ 0.75 (Jaccard/ARI); RT ~ distância com efeitos após controles.
- EEG/fMRI: RSA média ρ ≥ 0.30 em ≥ 2 datasets; N400 decresce com força/distância SWOW.
- Clínica: ΔAUC ≥ 0.05 e NRI ≥ 0.10 vs. baseline; quando possível, validação externa.
- Robustez: efeitos mantidos sob modelos nulos e perturbações; seeds fixos; relatórios reprodutíveis.

## 5) Riscos & Mitigações (Investigativo Profundo)
- Viés lexical/frequência → controlar por frequência, concreteness, polissêmia.
- Artefatos de projeção (UMAP) → reportar métricas no espaço original; checar PCA/t-SNE.
- Shift cultural/idiomático → replicar com SWOW multi-idioma; análise de sensibilidade.
- Overfitting neuro → pré-registros, RSA adequada, correção de múltiplos testes.

## 6) Entregáveis e governança de pesquisa
- Notebooks 07–10 de validação (ver plano em `NHB_Symbolic_Mainfold/VALIDATION_PLAN.md`).
- OSF Components por paper (dados derivados + scripts); linkar ao Zenodo (release por submissão).
- Reprodutibilidade: ambiente pinado, `Reset & Run-All`, figuras 300 dpi salvas via código.

## 7) Checklist operacional (ticável)
- [ ] Corrigir refs Git e push v1.5 (código NHB) ao GitHub
- [ ] Criar branches por paper
- [ ] Submeter Paper de Métodos (NHB)
- [ ] Pré-registrar RSA (OSF)
- [ ] Rodar validação semântica (comunidades/estabilidade)
- [ ] Executar EEG N400 (≥1 dataset público)
- [ ] Rodar RSA-fMRI (≥2 datasets narrativos)
- [ ] Relatório de Robustez/Modelos nulos
- [ ] Normativo + Clínico I
- [ ] Empacotar releases (Zenodo) e componentes (OSF)
