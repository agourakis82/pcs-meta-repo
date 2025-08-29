
# spec_PCS-HELIO (v1.1, 2025-08-23)

**Escopo:** especificação mínima executável do módulo PCS‑HELIO (dados, janelas, modelos, reporting).

## Dados (fontes públicas; formatos)
- Kp (NOAA/SWPC; 3h; JSON/CSV)
- Dst/AE (WDC Kyoto; 1h/min; TXT/CSV)
- OMNI (SPDF/NASA; 1 min/1h; CDF/CSV): IMF Bz, V, Np, Pdyn
- F10.7 (NOAA/NRC; diário; CSV)
- DONKI (NASA; eventos CMEs/flares/GST; JSON)
- Texto com timestamp (GDELT: títulos/URLs; CSV/BigQuery)
- ZuCo (EEG+eye tracking; licença pública; TSV)

## Janelas e eventos
- Eventos: Kp ≥ 5 (tempestade); Dst ≤ −50 (moderada) e ≤ −100 nT (forte).
- Janela SEA: −3…+3 dias (default); sensibilidade (−5…+5).
- Lags candidatos: 0–7 dias (epidemiológico).

## Métricas de resposta (AG5/KEC)
- Entropia de transição (Markov 1‑ordem sobre tokens/lemmas)
- Curvatura (Forman rápida; Ollivier amostral para *subset*)
- Coerência local (cosine/SLM) e escore composto (z‑score)

## Modelos
- SEA: média alinhada ao evento; baseline dia calmo; IC bootstrap; FDR.
- ARIMAX/VAR Bayes: estacionariedade; IRFs; heterogeneidade por idioma/latitude.
- ZuCo: regressões mistas (sujeito/sentença) custo~AG5.

## Falsificações / Ablations
- Placebo lags; shuffle de ordem; grafos nulos (preserva grau).
- Perturbação de stopwords e *downsampling* de frequência.

## Reporting mínimo
N eventos; N títulos; ΔKEC (média; IC; p_FDR); IRFs (coef/IC); ZuCo (β/d/IC).
Figuras: (1) tempestade média ΔKEC; (2) IRFs; (3) ZuCo (raincloud/efeito).

## Proveniência e licenças
Proveniência YAML por fonte; MIT (código); CC BY 4.0 (derivados).
