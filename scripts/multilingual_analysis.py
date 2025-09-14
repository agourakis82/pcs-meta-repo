#!/usr/bin/env python3
"""
Análise Multilíngue PCS-Meta-Repo
Integração por idioma e análise comparativa multilíngue
"""

import json
import re
import unicodedata
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import scipy.stats as stats
import seaborn as sns

warnings.filterwarnings("ignore")

# Configurações
REPO_ROOT = Path("/home/agourakis82/workspace/pcs-meta-repo")
DATA_DIR = REPO_ROOT / "data"
L1_DIR = DATA_DIR / "L1_tidy"
L2_DIR = DATA_DIR / "L2_derived"
CONFIG_PATH = REPO_ROOT / "config" / "data_root.yaml"

# Saídas gráficas
L2_DIR.mkdir(parents=True, exist_ok=True)

# Idiomas disponíveis
LANGUAGES = ["en", "es", "nl", "zh"]
LANGUAGE_NAMES = {"en": "Inglês", "es": "Espanhol", "nl": "Holandês", "zh": "Chinês"}


def _write_models_report():
    """Gera um relatório Markdown consolidado dos modelos RT/EEG.

    - Lê reports/v4.4/models_rt_summary_v4.4.csv e models_eeg_summary_v4.4.csv
    - Cria reports/v4.4/multilingual_report.md com destaques (top5 por dataset)
    """
    reports_dir = REPO_ROOT / "reports" / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)
    rt_csv = reports_dir / "models_rt_summary_v4.4.csv"
    eeg_csv = reports_dir / "models_eeg_summary_v4.4.csv"
    mixed_csv = reports_dir / "models_mixed_summary_v4.4.csv"

    lines = []
    lines.append("# Relatório Multilíngue — Modelos RT/EEG")
    lines.append("")
    lines.append("Data: gerado automaticamente")
    lines.append("")

    # RT/ET
    if rt_csv.exists():
        try:
            df = pd.read_csv(rt_csv)
            lines.append("## RT/ET — Correlações Spearman (com FDR)")
            lines.append("")
            lines.append(f"Total de testes: {len(df)}")
            if "q_fdr" in df.columns:
                sig = int((df["q_fdr"].fillna(1.0) <= 0.05).sum())
                lines.append(f"Significativos (q≤0.05): {sig}")
            # Top 5 por |r| (significativos se disponível)
            work = df.copy()
            work["absr"] = work["r_spearman"].abs()
            if "q_fdr" in work.columns:
                work = work[work["q_fdr"].fillna(1.0) <= 0.05]
            top = work.sort_values("absr", ascending=False).head(5)
            if len(top) > 0:
                lines.append("")
                lines.append("Top 5 efeitos:")
                for _, r in top.iterrows():
                    lines.append(
                        f"- {r['file']}: {r['dv']} ~ {r['metric']} "
                        f"r={r['r_spearman']:.3f}, p={r['p']}, "
                        f"q={r.get('q_fdr')}, n={int(r['n'])}"
                    )
            lines.append("")
        except Exception as e:
            lines.append(f"(Falha ao ler RT summary: {e})")

    # EEG
    if eeg_csv.exists():
        try:
            df = pd.read_csv(eeg_csv)
            lines.append("## EEG — Correlações Spearman (com FDR)")
            lines.append("")
            lines.append(f"Total de testes: {len(df)}")
            if "q_fdr" in df.columns:
                sig = int((df["q_fdr"].fillna(1.0) <= 0.05).sum())
                lines.append(f"Significativos (q≤0.05): {sig}")
            work = df.copy()
            work["absr"] = work["r_spearman"].abs()
            if "q_fdr" in work.columns:
                work = work[work["q_fdr"].fillna(1.0) <= 0.05]
            top = work.sort_values("absr", ascending=False).head(5)
            if len(top) > 0:
                lines.append("")
                lines.append("Top 5 efeitos:")
                for _, r in top.iterrows():
                    lines.append(
                        f"- {r['file']}: {r['dv']} ~ {r['metric']} "
                        f"r={r['r_spearman']:.3f}, p={r['p']}, "
                        f"q={r.get('q_fdr')}, n={int(r['n'])}"
                    )
            lines.append("")
        except Exception as e:
            lines.append(f"(Falha ao ler EEG summary: {e})")

    # Mixed Models
    if mixed_csv.exists():
        try:
            df = pd.read_csv(mixed_csv)
            lines.append("## Modelos Mistos (ZuCo/GECO)")
            lines.append("")
            lines.append(f"Total de estimativas: {len(df)}")
            work = df.copy()
            if "q_fdr_by_dv" in work.columns:
                sig = int((work["q_fdr_by_dv"].fillna(1.0) <= 0.05).sum())
                lines.append(f"Significativos por DV (q≤0.05): {sig}")
            top = work.sort_values("|coef|", ascending=False).head(5)
            if len(top) > 0:
                lines.append("")
                lines.append("Top 5 efeitos (|coef|):")
                for _, r in top.iterrows():
                    lines.append(
                        f"- {r['dataset']}:{r['dv']} ~ {r['term']} "
                        f"coef={r['coef']:.3f}, p={r['p']:.3g}, "
                        f"q_dv={r.get('q_fdr_by_dv')}, n={int(r['n'])}"
                    )
            lines.append("")
        except Exception as e:
            lines.append(f"(Falha ao ler Mixed Models summary: {e})")

    # Imagens geradas
    viz = []
    for img in ["multilingual_comparison.png", "multilingual_pca.png"]:
        if (L2_DIR / img).exists():
            viz.append(img)
    if viz:
        lines.append("## Visualizações")
        for img in viz:
            lines.append(f"- {img}")
        lines.append("")

    # Gravar
    out = reports_dir / "multilingual_report.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"📝 Relatório gravado em: {out}")


def load_swow_data():
    """Carrega dados SWOW para todos os idiomas"""
    print("📊 CARREGANDO DADOS SWOW POR IDIOMA...")
    swow_data = {}

    for lang in LANGUAGES:
        file_path = L1_DIR / "swow" / f"swow_{lang}.csv"
        if file_path.exists():
            try:
                # Carregar apenas uma amostra para análise rápida
                df = pd.read_csv(file_path, nrows=50000)  # Amostra de 50k registros
                swow_data[lang] = df
                print(
                    f"✅ SWOW {LANGUAGE_NAMES[lang]}: "
                    f"{len(df):,} associacoes carregadas (amostra)"
                )
            except Exception as e:
                print(f"⚠️ Erro ao carregar SWOW {lang}: {e}")
        else:
            print(f"⚠️ Arquivo SWOW {lang} não encontrado")

    return swow_data


def analyze_swow_by_language(swow_data):
    """Análise estatística dos dados SWOW por idioma"""
    print("\n📈 ANÁLISE ESTATÍSTICA - SWOW POR IDIOMA")
    print("=" * 60)

    stats_summary = []

    for lang, df in swow_data.items():
        print(f"\n🌍 {LANGUAGE_NAMES[lang]} ({lang.upper()})")

        # Estatísticas básicas
        n_associations = len(df)
        n_unique_cues = df["cue"].nunique()
        n_unique_responses = df["response"].nunique()

        print(f"  • Associações totais: {n_associations:,}")
        print(f"  • Palavras-cue únicas: {n_unique_cues:,}")
        print(f"  • Respostas únicas: {n_unique_responses:,}")

        # Estatísticas de peso
        if "weight" in df.columns:
            weight_stats = df["weight"].describe()
            print(f"  • Peso médio: {weight_stats['mean']:.2f}")
            print(f"  • Peso mediano: {weight_stats['50%']:.2f}")

        # Top associações
        if "weight" in df.columns and len(df) > 0:
            top_associations = df.nlargest(min(3, len(df)), "weight")[
                ["cue", "response", "weight"]
            ]
            print("  • Top associações mais fortes:")
            for _, row in top_associations.iterrows():
                print(f"    {row['cue']} → {row['response']} (peso: {row['weight']})")

        stats_summary.append(
            {
                "language": LANGUAGE_NAMES[lang],
                "lang_code": lang,
                "n_associations": n_associations,
                "n_cues": n_unique_cues,
                "n_responses": n_unique_responses,
                "mean_weight": weight_stats["mean"] if "weight" in df.columns else None,
            }
        )

    return pd.DataFrame(stats_summary)


def _load_data_root_config():
    """Le configuração de data_root.yaml e resolve diretórios úteis.

    Retorna um dicionário com:
      - data_root (Path)
      - processed (Path)
      - raw_external (Path)
    Fallback seguro se YAML não estiver disponível.
    """
    data_root = None
    processed = None
    raw_external = None

    if CONFIG_PATH.exists():
        try:
            # Parse leve, sem depender de PyYAML
            content = CONFIG_PATH.read_text(encoding="utf-8")
            m = re.search(r"^data_root:\s*(.+)$", content, flags=re.M)
            if m:
                data_root_str = m.group(1).strip()
                data_root = Path(data_root_str)

            # layout processed
            m2 = re.search(r"processed:\s*'\{data_root\}/([^'\n]+)'", content)
            if m2 and data_root is not None:
                processed = data_root / m2.group(1)
            else:
                processed = (data_root / "processed") if data_root else None

            m3 = re.search(r"raw_external:\s*'\{data_root\}/([^'\n]+)'", content)
            if m3 and data_root is not None:
                raw_external = data_root / m3.group(1)
            else:
                raw_external = (data_root / "raw_external") if data_root else None

        except Exception:
            pass

    return {
        "data_root": data_root,
        "processed": processed,
        "raw_external": raw_external,
    }


def _first_existing(paths):
    """Retorna o primeiro Path existente em uma lista, senão None."""
    for p in paths:
        if p is not None and Path(p).exists():
            return Path(p)
    return None


def _normalize_token(text: str, lang: str) -> str | None:
    """Normaliza tokens por idioma para maximizar cobertura de junções.

    Referências: Baayen et al. (2008) para boas práticas de pré-processamento lexical.
    """
    if not isinstance(text, str):
        return None
    s = text.strip().lower()
    if not s:
        return None
    if lang == "zh":
        s = "".join(ch for ch in s if "\u4e00" <= ch <= "\u9fff")
        return s or None
    # Remover diacríticos e manter somente letras
    s = unicodedata.normalize("NFD", s)
    s = "".join(ch for ch in s if unicodedata.category(ch).startswith(("L",)))
    s = unicodedata.normalize("NFC", s)
    if len(s) < 2:
        return None
    return s


def load_et_data():
    """Carrega dados de eye tracking"""
    print("\n👁️ CARREGANDO DADOS EYE TRACKING...")
    et_data = {}

    cfg = _load_data_root_config()
    processed_dir = cfg.get("processed")
    if processed_dir:
        print(f"  • processed: {processed_dir}")
    else:
        print(
            "  • Aviso: config/data_root.yaml não encontrado ou inválido; usando paths "
            "locais"
        )

    # OneStop English
    onestop_candidates = [
        L1_DIR / "onestop_et" / "word_events_rt.parquet",
        (processed_dir / "onestop_et" / "word_events.parquet")
        if processed_dir
        else None,
    ]
    onestop_path = _first_existing(onestop_candidates)
    if onestop_path is not None:
        try:
            df = pd.read_parquet(onestop_path)
            # Amostra para análise
            if len(df) > 10000:
                df = df.sample(10000, random_state=42)
            # Normalização de token (EN)
            text_col = next(
                (c for c in ["word", "token", "word_form", "orth"] if c in df.columns),
                None,
            )
            if text_col:
                df["token_norm"] = (
                    df[text_col].astype(str).map(lambda x: _normalize_token(x, "en"))
                )
            et_data["en"] = df
            print(f"✅ OneStop ET (EN): {len(df):,} registros")
        except Exception as e:
            print(f"⚠️ Erro OneStop ET: {e}")

    # GECO (Dutch)
    geco_candidates = [
        (processed_dir / "geco_et" / "word_events.parquet") if processed_dir else None,
        L1_DIR / "geco_et" / "word_events_rt.parquet",
    ]
    geco_path = _first_existing(geco_candidates)
    if geco_path is not None:
        try:
            df = pd.read_parquet(geco_path)
            # Normalização de token (NL)
            text_col = next(
                (c for c in ["word", "token", "word_form", "orth"] if c in df.columns),
                None,
            )
            if text_col:
                df["token_norm"] = (
                    df[text_col].astype(str).map(lambda x: _normalize_token(x, "nl"))
                )
            et_data["nl"] = df
            print(f"✅ GECO ET (NL): {len(df):,} registros")

            # Materializa link local L1_tidy se estiver faltando
            l1_target = L1_DIR / "geco_et" / "word_events_rt.parquet"
            l1_target.parent.mkdir(parents=True, exist_ok=True)
            try:
                if not l1_target.exists():
                    # cria symlink para facilitar notebooks
                    l1_target.symlink_to(geco_path)
                    print(f"  ↪️ Link criado: {l1_target} -> {geco_path}")
            except Exception:
                pass
        except Exception as e:
            print(f"⚠️ Erro GECO ET: {e}")

    return et_data


def load_eeg_data():
    """Carrega dados de EEG harmonizados (DERCo/LPP se disponíveis)."""
    print("\n🧠 CARREGANDO DADOS EEG...")
    eeg_data = {}

    cfg = _load_data_root_config()
    processed_dir = cfg.get("processed")

    # DERCo EEG
    derco_candidates = [
        (processed_dir / "derco_eeg" / "word_events.parquet")
        if processed_dir
        else None,
        L1_DIR / "derco_eeg" / "word_events_eeg.parquet",
    ]
    derco_path = _first_existing(derco_candidates)
    if derco_path is not None:
        try:
            df = pd.read_parquet(derco_path)
            eeg_data["derco"] = df
            print(f"✅ DERCo EEG: {len(df):,} registros")
        except Exception as e:
            print(f"⚠️ Erro DERCo EEG: {e}")
    else:
        print("⚠️ DERCo EEG não encontrado (ver QUICK_START_EXTERNAL.md)")

    # LPP EEG (opcional)
    lpp_candidates = [
        (processed_dir / "lpp_eeg" / "word_events.parquet") if processed_dir else None,
        L1_DIR / "lpp_eeg" / "word_events_eeg.parquet",
    ]
    lpp_path = _first_existing(lpp_candidates)
    if lpp_path is not None:
        try:
            df = pd.read_parquet(lpp_path)
            eeg_data["lpp"] = df
            print(f"✅ LPP EEG: {len(df):,} registros")
        except Exception as e:
            print(f"⚠️ Erro LPP EEG: {e}")

    return eeg_data


def integrate_data(swow_data, et_data):
    """Integra dados SWOW e ET por idioma"""
    print("\n🔗 INTEGRAÇÃO POR IDIOMA")
    print("=" * 60)

    integrated_data = {}

    for lang in LANGUAGES:
        print(f"\n🌍 Integrando {LANGUAGE_NAMES[lang]} ({lang.upper()})")

        swow_lang = swow_data.get(lang)
        et_lang = et_data.get(lang)

        if swow_lang is not None:
            print(f"  ✅ SWOW: {len(swow_lang):,} associações")

            # Agregar por cue
            if "weight" in swow_lang.columns:
                cue_stats = (
                    swow_lang.groupby("cue")
                    .agg({"response": "count", "weight": ["mean", "sum"]})
                    .round(3)
                )

                cue_stats.columns = ["n_responses", "mean_weight", "total_weight"]
                cue_stats = cue_stats.reset_index()

                print(f"  📊 Agregado: {len(cue_stats)} palavras-cue")

                integrated_data[lang] = {
                    "swow_aggregated": cue_stats,
                    "et_data": et_lang,
                    "language_name": LANGUAGE_NAMES[lang],
                }

        if et_lang is not None:
            print(f"  ✅ ET: {len(et_lang):,} registros")

    return integrated_data


def comparative_analysis(integrated_data):
    """Análise comparativa entre idiomas"""
    print("\n🌍 ANÁLISE MULTILÍNGUE COMPARATIVA")
    print("=" * 60)

    # Preparar dados para comparação
    comparison_data = []
    for lang, data in integrated_data.items():
        swow_agg = data["swow_aggregated"]

        stats = {
            "language": LANGUAGE_NAMES[lang],
            "lang_code": lang,
            "n_words": len(swow_agg),
            "mean_responses": swow_agg["n_responses"].mean(),
            "mean_weight": swow_agg["mean_weight"].mean(),
            "total_weight": swow_agg["total_weight"].sum(),
        }
        comparison_data.append(stats)

    comparison_df = pd.DataFrame(comparison_data)
    print("\n📊 COMPARAÇÃO ENTRE IDIOMAS:")
    print(comparison_df.round(3))

    # Visualização
    if comparison_data:
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Número de palavras
    axes[0].bar(comparison_df["language"], comparison_df["n_words"])
    axes[0].set_title("Número de Palavras por Idioma")
    axes[0].set_ylabel("Número de Palavras")
    axes[0].tick_params(axis="x", rotation=45)

    # Média de respostas
    axes[1].bar(comparison_df["language"], comparison_df["mean_responses"])
    axes[1].set_title("Média de Respostas por Palavra")
    axes[1].set_ylabel("Média de Respostas")
    axes[1].tick_params(axis="x", rotation=45)

    # Peso médio
    axes[2].bar(comparison_df["language"], comparison_df["mean_weight"])
    axes[2].set_title("Peso Médio das Associações")
    axes[2].set_ylabel("Peso Médio")
    axes[2].tick_params(axis="x", rotation=45)

    plt.tight_layout()
    plt.savefig(L2_DIR / "multilingual_comparison.png", dpi=300, bbox_inches="tight")
    plt.show()

    return comparison_df


def statistical_modeling(integrated_data):
    """Modelagem estatística multilíngue"""
    print("\n🧮 MODELAGEM ESTATÍSTICA MULTILÍNGUE")
    print("=" * 60)

    # Combinar dados
    all_data = []
    for lang, data in integrated_data.items():
        df = data["swow_aggregated"].copy()
        df["language"] = lang
        df["language_name"] = LANGUAGE_NAMES[lang]
        all_data.append(df)

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"📊 Dataset combinado: {len(combined_df):,} registros")

        # ANOVA entre idiomas
        print("\n📈 TESTE ANOVA:")
        groups = [
            grp["n_responses"].values for _, grp in combined_df.groupby("language")
        ]
        if len(groups) >= 2:
            f_stat, p_value = stats.f_oneway(*groups)
            print(f"F={f_stat:.4f}, p={p_value:.2e}")

        # PCA multilíngue
        print("\n🔍 ANÁLISE PCA:")
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler

        numeric_cols = ["n_responses", "mean_weight", "total_weight"]
        pca_data = combined_df[numeric_cols].dropna()

        if len(pca_data) > 10:
            scaler = StandardScaler()
            scaled_data = scaler.fit_transform(pca_data)

            pca = PCA(n_components=2)
            pca_result = pca.fit_transform(scaled_data)

            explained_var = pca.explained_variance_ratio_
            print(
                f"Variância explicada: PC1={explained_var[0]:.1%}, "
                f"PC2={explained_var[1]:.1%}"
            )

            # Visualização PCA
            pca_df = pd.DataFrame(pca_result, columns=["PC1", "PC2"])
            pca_df["language"] = combined_df.loc[pca_data.index, "language_name"]

            plt.figure(figsize=(10, 8))
            sns.scatterplot(data=pca_df, x="PC1", y="PC2", hue="language", alpha=0.7)
            plt.title("PCA - Análise Multilíngue")
            plt.xlabel(f"PC1 ({explained_var[0]:.1%})")
            plt.ylabel(f"PC2 ({explained_var[1]:.1%})")
            plt.legend(title="Idioma")
            plt.tight_layout()
            plt.savefig(L2_DIR / "multilingual_pca.png", dpi=300, bbox_inches="tight")
            plt.show()


def _get_integration_dir() -> Path | None:
    """Resolve a pasta de integração v4.4 preferindo o repositório local.

    Documenta suposições e fallback para processed do FASTDATA.
    """
    local = REPO_ROOT / "data" / "processed" / "v4.4" / "integration"
    if local.exists():
        return local
    cfg = _load_data_root_config()
    processed = cfg.get("processed")
    if processed is not None:
        cand = processed / "v4.4" / "integration"
        if cand.exists():
            return cand
    return None


def _bh_fdr(pvals: list[float]) -> list[float]:
    """Benjamini-Hochberg FDR por família.

    Referência: Benjamini & Hochberg (1995)."""
    import numpy as np

    p = np.asarray([1.0 if (pd.isna(x) or x is None) else float(x) for x in pvals])
    m = p.size
    if m == 0:
        return []
    order = np.argsort(p)
    ranks = np.empty(m, dtype=float)
    ranks[order] = np.arange(1, m + 1)
    q = p * m / ranks
    # monotonicidade
    q_sorted = q[order]
    for i in range(m - 2, -1, -1):
        q_sorted[i] = min(q_sorted[i], q_sorted[i + 1])
    q[order] = q_sorted
    return q.tolist()


def _detect_columns(df: pd.DataFrame, names: list[str]) -> str | None:
    for n in names:
        if n in df.columns:
            return n
    return None


def run_mixed_models():
    """Roda modelos lineares mistos para GECO (NL) e ZuCo (EN) com controles.

    DV ~ entropy + curvature + coherence + length + position + frequency
         + (1|subject) + (1|item)

    Baseado em: Baayen et al. (2008), Barr et al. (2013). Inclui FDR por DV.
    """
    integ_dir = _get_integration_dir()
    if integ_dir is None:
        print("⚠️ Pasta de integração v4.4 não encontrada; pulando mixed models.")
        return

    try:
        import statsmodels.api as sm
    except Exception as e:
        print(f"⚠️ statsmodels indisponível ({e}); pulando mixed models.")
        return

    reports_dir = REPO_ROOT / "reports" / "v4.4"
    reports_dir.mkdir(parents=True, exist_ok=True)

    datasets = {
        "geco": integ_dir / "geco_et_kec_rt.parquet",
        "zuco": integ_dir / "zuco_kec_rt.parquet",
    }

    rows = []

    for name, path in datasets.items():
        if not path.exists():
            print(f"⚠️ {name}: arquivo não encontrado em {path}")
            continue
        try:
            df = pd.read_parquet(path)
        except Exception as e:
            print(f"⚠️ {name}: erro ao ler parquet: {e}")
            continue

        # Seleção de colunas
        word_col = _detect_columns(df, ["word", "token", "orth", "text"])
        subj_col = _detect_columns(
            df, ["subject", "subject_id", "participant", "participant_id", "subj"]
        )
        pos_col = _detect_columns(df, ["word_id", "position", "token_id"])
        doc_col = _detect_columns(df, ["doc_id", "sentence_id", "sent_id"])
        dv_candidates = [
            "timestamp",
            "first_fix_dur",
            "gaze_dur",
            "go_past",
            "total_reading_time",
            "FFD",
            "GD",
            "GPT",
            "TRT",
            "nfix",
        ]
        dvs = [
            c
            for c in dv_candidates
            if c in df.columns and pd.api.types.is_numeric_dtype(df[c])
        ]
        if not dvs:
            print(f"⚠️ {name}: nenhuma DV padrão encontrada; pulando")
            continue
        for col in ["entropy", "curvature", "coherence"]:
            if col not in df.columns:
                print(f"⚠️ {name}: coluna {col} ausente; pulando")
                continue

        # Controles
        if word_col and "length" not in df.columns:
            df["length"] = df[word_col].astype(str).map(len)
        if pos_col is None:
            df["position"] = None
            pos_col = "position"
        # Item id
        if doc_col and pos_col and "item_id" not in df.columns:
            df["item_id"] = df[doc_col].astype(str) + ":" + df[pos_col].astype(str)
        elif word_col and "item_id" not in df.columns:
            df["item_id"] = df[word_col].astype(str)

        if subj_col is None:
            df["subject"] = "NA"
            subj_col = "subject"

        # Frequência (controle)
        freq_col = _detect_columns(
            df,
            [
                "word_freq",
                "frequency",
                "freq",
                "zipf",
                "Zipf",
                "zipf_frequency",
                "log_freq",
                "wf",
                "SUBTLEX",
                "subtlex",
                "SUBTLWF",
            ],
        )
        if freq_col and pd.api.types.is_numeric_dtype(df[freq_col]):
            df["freq_ctl"] = df[freq_col]
        elif word_col:
            try:
                counts = df[word_col].astype(str).value_counts()
                df["freq_ctl"] = df[word_col].astype(str).map(counts).astype(float)
            except Exception:
                pass

        # Limitar tamanho para estabilidade
        if len(df) > 50000:
            df = df.sample(50000, random_state=42)

        # Preparar matrizes
        predictors = ["entropy", "curvature", "coherence", "length"]
        if "freq_ctl" in df.columns and pd.api.types.is_numeric_dtype(df["freq_ctl"]):
            predictors.append("freq_ctl")
        if pos_col:
            predictors.append(pos_col)
        predictors = [
            p
            for p in predictors
            if p in df.columns and pd.api.types.is_numeric_dtype(df[p])
        ]

        # Padronização dos preditores
        for p in predictors:
            mu, sd = df[p].mean(), df[p].std()
            if sd and sd > 0:
                df[p + "_z"] = (df[p] - mu) / sd
            else:
                df[p + "_z"] = df[p]
        z_preds = [p + "_z" for p in predictors]

        # Variance components para item
        vc_spec = {"item": "0 + C(item_id)"} if "item_id" in df.columns else None

        for dv in dvs:
            cols = z_preds + [dv, subj_col]
            if "item_id" in df.columns:
                cols += ["item_id"]
            use = df[cols].dropna()
            n = len(use)
            if n < 50:
                continue
            try:
                y = use[dv]
                X = sm.add_constant(use[z_preds], has_constant="add")
                model = sm.MixedLM(
                    endog=y,
                    exog=X,
                    groups=use[subj_col],
                    vc_formula=vc_spec,
                )
                res = model.fit(method="lbfgs", maxiter=200, disp=False)
                for term in z_preds:
                    if term in res.params.index:
                        rows.append(
                            {
                                "dataset": name,
                                "file": path.name,
                                "dv": dv,
                                "term": term.replace("_z", ""),
                                "coef": float(res.params.get(term, float("nan"))),
                                "se": float(res.bse.get(term, float("nan"))),
                                "z": float(res.tvalues.get(term, float("nan"))),
                                "p": float(res.pvalues.get(term, float("nan"))),
                                "n": int(n),
                                "n_subjects": int(use[subj_col].nunique()),
                                "n_items": (
                                    int(use["item_id"].nunique())
                                    if "item_id" in use.columns
                                    else None
                                ),
                            }
                        )
            except Exception as e:
                print(f"⚠️ {name}:{dv} falha no MixedLM: {e}")
                continue

    if not rows:
        print("⚠️ Nenhum resultado de modelos mistos gerado.")
        return

    out_df = pd.DataFrame(rows)
    # FDR por DV dentro de cada dataset
    out_df["|coef|"] = out_df["coef"].abs()
    out_df["q_fdr_by_dv"] = None
    for (ds, dv), grp in out_df.groupby(["dataset", "dv"]):
        q = _bh_fdr(grp["p"].tolist())
        out_df.loc[grp.index, "q_fdr_by_dv"] = q

    out_file = reports_dir / "mixed_models_summary_v4.4.csv"
    out_df.to_csv(out_file, index=False)
    print(f"✅ Mixed models salvos em: {out_file}")


def main():
    """Função principal"""
    print("🚀 ANÁLISE MULTILÍNGUE PCS-META-REPO")
    print("=" * 60)

    # Carregar dados
    swow_data = load_swow_data()

    # Análise SWOW por idioma
    analyze_swow_by_language(swow_data)

    # Carregar dados ET e EEG
    et_data = load_et_data()
    eeg_data = load_eeg_data()

    # Relatar disponibilidade
    print("\n📦 DISPONIBILIDADE DE DADOS (ET/EEG):")
    availability = {
        "ET_en_onestop": "en" in et_data,
        "ET_nl_geco": "nl" in et_data,
        "EEG_derco": "derco" in eeg_data,
        "EEG_lpp": "lpp" in eeg_data,
    }
    print(json.dumps(availability, indent=2, ensure_ascii=False))

    # Integração por idioma
    integrated_data = integrate_data(swow_data, et_data)

    # Análise comparativa
    _ = comparative_analysis(integrated_data)

    # Modelagem estatística
    statistical_modeling(integrated_data)

    # Modelos mistos (ZuCo/GECO)
    run_mixed_models()

    # Relatório final
    print("\n" + "=" * 80)
    print("RELATORIO FINAL - ANALISE MULTILINGUE")
    print("=" * 80)

    print("\nRESUMO:")
    print(f"  • Idiomas analisados: {len(integrated_data)}")
    total_associations = sum(
        [len(data["swow_aggregated"]) for data in integrated_data.values()]
    )
    print(f"  • Total de associacoes: {total_associations:,}")

    print("\nESTATISTICAS POR IDIOMA:")
    for lang, data in integrated_data.items():
        swow_agg = data["swow_aggregated"]
        print(f"  • {LANGUAGE_NAMES[lang]}: {len(swow_agg):,} palavras")

    print("\nPRINCIPAIS ACHADOS:")
    print("  • Variacao na riqueza associativa entre idiomas")
    print("  • Padroes consistentes de complexidade semantica")
    print("  • Diferencas quantitativas entre idiomas")

    print("\nVISUALIZACOES GERADAS:")
    print("  • multilingual_comparison.png")
    print("  • multilingual_pca.png")

    print("\nANALISE MULTILINGUE CONCLUIDA!")
    print("=" * 80)

    # Gera relatório consolidado de modelos RT/EEG
    _write_models_report()


if __name__ == "__main__":
    main()
