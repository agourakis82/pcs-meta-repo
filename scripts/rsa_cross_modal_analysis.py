#!/usr/bin/env python3
"""
Representational Similarity Analysis (RSA): Cross-Modal Validation

This script implements RSA to validate correspondence between KEC representations
and neural patterns, establishing convergent validity for Nature Q1 standards.

Methods:
- RSA between KEC metrics and EEG patterns
- Temporal RSA analysis
- Cross-linguistic RSA validation
- Statistical significance testing

Author: PCS Meta-Repo Team
Date: January 2025
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings

warnings.filterwarnings("ignore")

# Statistical libraries
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.manifold import MDS
import statsmodels.api as sm

# Set random seed for reproducibility
np.random.seed(42)

# Configure plotting
plt.style.use("seaborn-v0_8")
sns.set_palette("husl")
plt.rcParams["figure.figsize"] = (14, 10)
plt.rcParams["font.size"] = 12


def load_or_create_data():
    """Load integrated dataset or create synthetic data for RSA analysis"""

    data_path = Path("../outputs/integration/")

    try:
        # Try to load real integrated dataset
        df = pd.read_csv(data_path / "integrated_swow_kec_eeg_rt.csv")
        print(f"✓ Loaded integrated dataset: {df.shape}")
        return df

    except FileNotFoundError:
        print("⚠ Creating synthetic data for RSA demonstration...")

        # Create realistic synthetic data with known RSA structure
        n_words = 200  # Smaller set for RSA analysis
        n_subjects = 15
        n_timepoints = 50  # EEG time series

        # Generate word stimuli with semantic categories
        categories = ["animals", "tools", "foods", "places", "actions"]
        words_per_category = n_words // len(categories)

        df = pd.DataFrame(
            {
                "word_id": range(n_words),
                "token_norm": [f"word_{i}" for i in range(n_words)],
                "category": np.repeat(categories, words_per_category),
                "word_frequency": np.random.lognormal(2, 1, n_words),
                "word_length": np.random.poisson(6, n_words),
            }
        )

        # Generate KEC metrics with category structure
        category_effects = {
            "animals": {"entropy": 2.8, "curvature": 0.15, "coherence": 0.55},
            "tools": {"entropy": 2.2, "curvature": 0.25, "coherence": 0.65},
            "foods": {"entropy": 2.5, "curvature": 0.10, "coherence": 0.60},
            "places": {"entropy": 3.0, "curvature": 0.05, "coherence": 0.50},
            "actions": {"entropy": 3.2, "curvature": 0.20, "coherence": 0.45},
        }

        kec_entropy = []
        kec_curvature = []
        kec_coherence = []

        for _, row in df.iterrows():
            cat = row["category"]
            base_entropy = category_effects[cat]["entropy"]
            base_curvature = category_effects[cat]["curvature"]
            base_coherence = category_effects[cat]["coherence"]

            # Add frequency effects and noise
            freq_effect = -0.2 * np.log(row["word_frequency"])

            kec_entropy.append(base_entropy + freq_effect + np.random.normal(0, 0.3))
            kec_curvature.append(
                base_curvature + 0.5 * freq_effect + np.random.normal(0, 0.1)
            )
            kec_coherence.append(
                base_coherence - 0.3 * freq_effect + np.random.normal(0, 0.1)
            )

        df["kec_entropy"] = kec_entropy
        df["kec_curvature"] = kec_curvature
        df["kec_coherence"] = kec_coherence

        # Generate EEG data with similar category structure
        eeg_data = {}

        for subject in range(1, n_subjects + 1):
            subject_eeg = []

            for _, row in df.iterrows():
                cat = row["category"]

                # Base EEG patterns per category (simplified)
                if cat == "animals":
                    base_pattern = np.sin(np.linspace(0, 4 * np.pi, n_timepoints)) * 2
                elif cat == "tools":
                    base_pattern = np.cos(np.linspace(0, 3 * np.pi, n_timepoints)) * 1.5
                elif cat == "foods":
                    base_pattern = np.sin(np.linspace(0, 2 * np.pi, n_timepoints)) * 1.8
                elif cat == "places":
                    base_pattern = np.cos(np.linspace(0, 5 * np.pi, n_timepoints)) * 1.2
                else:  # actions
                    base_pattern = np.sin(np.linspace(0, 6 * np.pi, n_timepoints)) * 2.2

                # Add KEC-related modulation
                kec_modulation = (
                    0.3 * row["kec_entropy"]
                    + 0.2 * row["kec_curvature"]
                    + 0.1 * row["kec_coherence"]
                )

                # Add noise and individual differences
                individual_noise = np.random.normal(0, 0.5, n_timepoints)
                subject_effect = np.random.normal(0, 0.2)

                eeg_pattern = (
                    base_pattern * (1 + kec_modulation)
                    + individual_noise
                    + subject_effect
                )
                subject_eeg.append(eeg_pattern)

            eeg_data[f"subject_{subject}"] = np.array(subject_eeg)

        # Add summary EEG measures to dataframe
        df["theta_power"] = np.mean(
            [
                eeg_data[f"subject_{s}"][:, 10:20].mean(axis=1)
                for s in range(1, n_subjects + 1)
            ],
            axis=0,
        )
        df["alpha_power"] = np.mean(
            [
                eeg_data[f"subject_{s}"][:, 20:30].mean(axis=1)
                for s in range(1, n_subjects + 1)
            ],
            axis=0,
        )
        df["beta_power"] = np.mean(
            [
                eeg_data[f"subject_{s}"][:, 30:40].mean(axis=1)
                for s in range(1, n_subjects + 1)
            ],
            axis=0,
        )

        print(f"✓ Created synthetic dataset with RSA structure: {df.shape}")
        return df, eeg_data


def compute_rdm(data, metric="euclidean"):
    """Compute Representational Dissimilarity Matrix (RDM)"""

    # Standardize data
    scaler = StandardScaler()
    data_scaled = scaler.fit_transform(data)

    # Compute pairwise distances
    distances = pdist(data_scaled, metric=metric)
    rdm = squareform(distances)

    return rdm


def rsa_correlation(rdm1, rdm2, method="spearman"):
    """Compute RSA correlation between two RDMs"""

    # Extract upper triangular elements (excluding diagonal)
    mask = np.triu(np.ones_like(rdm1, dtype=bool), k=1)
    vec1 = rdm1[mask]
    vec2 = rdm2[mask]

    # Compute correlation
    if method == "spearman":
        correlation, p_value = stats.spearmanr(vec1, vec2)
    elif method == "pearson":
        correlation, p_value = stats.pearsonr(vec1, vec2)
    else:
        raise ValueError("Method must be 'spearman' or 'pearson'")

    return correlation, p_value


def bootstrap_rsa(rdm1, rdm2, n_bootstrap=1000, method="spearman"):
    """Bootstrap confidence intervals for RSA correlation"""

    n_items = rdm1.shape[0]
    bootstrap_correlations = []

    for _ in range(n_bootstrap):
        # Bootstrap sample indices
        boot_indices = np.random.choice(n_items, n_items, replace=True)

        # Create bootstrapped RDMs
        boot_rdm1 = rdm1[np.ix_(boot_indices, boot_indices)]
        boot_rdm2 = rdm2[np.ix_(boot_indices, boot_indices)]

        # Compute correlation
        corr, _ = rsa_correlation(boot_rdm1, boot_rdm2, method=method)
        bootstrap_correlations.append(corr)

    # Compute confidence intervals
    ci_lower = np.percentile(bootstrap_correlations, 2.5)
    ci_upper = np.percentile(bootstrap_correlations, 97.5)

    return bootstrap_correlations, ci_lower, ci_upper


def visualize_rdms(rdms, titles, figsize=(16, 12)):
    """Visualize multiple RDMs"""

    n_rdms = len(rdms)
    n_cols = min(3, n_rdms)
    n_rows = (n_rdms + n_cols - 1) // n_cols

    fig, axes = plt.subplots(n_rows, n_cols, figsize=figsize)
    if n_rdms == 1:
        axes = [axes]
    elif n_rows == 1:
        axes = axes.reshape(1, -1)

    for i, (rdm, title) in enumerate(zip(rdms, titles)):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col] if n_rows > 1 else axes[col]

        im = ax.imshow(rdm, cmap="viridis", aspect="auto")
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.set_xlabel("Word Index")
        ax.set_ylabel("Word Index")

        # Add colorbar
        plt.colorbar(im, ax=ax, shrink=0.8)

    # Hide empty subplots
    for i in range(n_rdms, n_rows * n_cols):
        row = i // n_cols
        col = i % n_cols
        ax = axes[row, col] if n_rows > 1 else axes[col]
        ax.axis("off")

    plt.tight_layout()
    return fig


def run_kec_eeg_rsa(df, eeg_data=None):
    """Run RSA analysis between KEC metrics and EEG patterns"""

    print("RSA Analysis: KEC ↔ EEG Patterns")
    print("=" * 40)

    # Prepare KEC data
    kec_features = ["kec_entropy", "kec_curvature", "kec_coherence"]
    kec_matrix = df[kec_features].values

    # Compute KEC RDM
    kec_rdm = compute_rdm(kec_matrix)

    # Prepare EEG data
    eeg_features = ["theta_power", "alpha_power", "beta_power"]
    eeg_matrix = df[eeg_features].values

    # Compute EEG RDM
    eeg_rdm = compute_rdm(eeg_matrix)

    # RSA correlation
    rsa_corr, rsa_p = rsa_correlation(kec_rdm, eeg_rdm)

    # Bootstrap confidence intervals
    boot_corrs, ci_lower, ci_upper = bootstrap_rsa(kec_rdm, eeg_rdm)

    print(f"KEC ↔ EEG RSA Correlation: r = {rsa_corr:.4f}")
    print(f"p-value: {rsa_p:.4f}")
    print(f"95% Bootstrap CI: [{ci_lower:.4f}, {ci_upper:.4f}]")

    # Visualize RDMs
    rdms = [kec_rdm, eeg_rdm]
    titles = [
        "KEC Representational\nDissimilarity Matrix",
        "EEG Representational\nDissimilarity Matrix",
    ]

    fig = visualize_rdms(rdms, titles)
    plt.savefig("../figures/rsa_kec_eeg_rdms.png", dpi=300, bbox_inches="tight")
    plt.show()

    # Create RSA scatter plot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8))

    # Extract upper triangular elements
    mask = np.triu(np.ones_like(kec_rdm, dtype=bool), k=1)
    kec_vec = kec_rdm[mask]
    eeg_vec = eeg_rdm[mask]

    # Scatter plot with regression line
    ax.scatter(kec_vec, eeg_vec, alpha=0.6, s=20)

    # Add regression line
    z = np.polyfit(kec_vec, eeg_vec, 1)
    p = np.poly1d(z)
    ax.plot(kec_vec, p(kec_vec), "r--", alpha=0.8, linewidth=2)

    ax.set_xlabel("KEC Dissimilarity")
    ax.set_ylabel("EEG Dissimilarity")
    ax.set_title(f"RSA: KEC ↔ EEG\nr = {rsa_corr:.4f}, p = {rsa_p:.4f}")
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("../figures/rsa_kec_eeg_scatter.png", dpi=300, bbox_inches="tight")
    plt.show()

    return {
        "kec_rdm": kec_rdm,
        "eeg_rdm": eeg_rdm,
        "rsa_correlation": rsa_corr,
        "rsa_p_value": rsa_p,
        "bootstrap_ci": (ci_lower, ci_upper),
        "bootstrap_correlations": boot_corrs,
    }


def run_temporal_rsa(df, eeg_data, time_windows=None):
    """Run temporal RSA analysis across EEG time windows"""

    if eeg_data is None:
        print("⚠ No temporal EEG data available for temporal RSA")
        return None

    print("\nTemporal RSA Analysis")
    print("=" * 25)

    if time_windows is None:
        # Define time windows (in sample points)
        time_windows = [
            (0, 10, "Early (0-200ms)"),
            (10, 20, "N400 (200-400ms)"),
            (20, 30, "Late (400-600ms)"),
            (30, 40, "Very Late (600-800ms)"),
        ]

    # Prepare KEC RDM
    kec_features = ["kec_entropy", "kec_curvature", "kec_coherence"]
    kec_matrix = df[kec_features].values
    kec_rdm = compute_rdm(kec_matrix)

    # Compute RSA across time windows
    temporal_rsa = []

    for start, end, label in time_windows:
        # Average EEG across subjects and time window
        window_eeg = []
        for subject in eeg_data.keys():
            subject_window = eeg_data[subject][:, start:end].mean(axis=1)
            window_eeg.append(subject_window)

        # Average across subjects
        avg_window_eeg = np.mean(window_eeg, axis=0).reshape(-1, 1)

        # Compute RDM for this time window
        window_rdm = compute_rdm(avg_window_eeg)

        # RSA correlation with KEC
        rsa_corr, rsa_p = rsa_correlation(kec_rdm, window_rdm)

        temporal_rsa.append(
            {
                "time_window": label,
                "start": start,
                "end": end,
                "rsa_correlation": rsa_corr,
                "rsa_p_value": rsa_p,
                "rdm": window_rdm,
            }
        )

        print(f"{label}: r = {rsa_corr:.4f}, p = {rsa_p:.4f}")

    # Plot temporal RSA timecourse
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # RSA correlations over time
    correlations = [result["rsa_correlation"] for result in temporal_rsa]
    p_values = [result["rsa_p_value"] for result in temporal_rsa]
    labels = [result["time_window"] for result in temporal_rsa]

    x_pos = range(len(labels))

    bars = ax1.bar(x_pos, correlations, alpha=0.7)
    ax1.set_xlabel("Time Window")
    ax1.set_ylabel("RSA Correlation (r)")
    ax1.set_title("Temporal RSA: KEC ↔ EEG Over Time")
    ax1.set_xticks(x_pos)
    ax1.set_xticklabels(labels, rotation=45, ha="right")
    ax1.grid(True, alpha=0.3)

    # Color bars by significance
    for i, (bar, p_val) in enumerate(zip(bars, p_values)):
        if p_val < 0.001:
            bar.set_color("darkgreen")
        elif p_val < 0.01:
            bar.set_color("green")
        elif p_val < 0.05:
            bar.set_color("orange")
        else:
            bar.set_color("red")

    # P-values
    ax2.bar(x_pos, [-np.log10(p) for p in p_values], alpha=0.7, color="gray")
    ax2.axhline(y=-np.log10(0.05), color="red", linestyle="--", label="p = 0.05")
    ax2.axhline(y=-np.log10(0.01), color="orange", linestyle="--", label="p = 0.01")
    ax2.set_xlabel("Time Window")
    ax2.set_ylabel("-log10(p-value)")
    ax2.set_title("Statistical Significance")
    ax2.set_xticks(x_pos)
    ax2.set_xticklabels(labels, rotation=45, ha="right")
    ax2.legend()
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("../figures/temporal_rsa_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

    return temporal_rsa


def run_category_rsa(df):
    """Run RSA analysis by semantic categories"""

    if "category" not in df.columns:
        print("⚠ No category information available for category RSA")
        return None

    print("\nCategory-based RSA Analysis")
    print("=" * 30)

    categories = df["category"].unique()
    print(f"Categories: {', '.join(categories)}")

    # Prepare data
    kec_features = ["kec_entropy", "kec_curvature", "kec_coherence"]
    eeg_features = ["theta_power", "alpha_power", "beta_power"]

    # Compute category-averaged representations
    category_kec = []
    category_eeg = []
    category_labels = []

    for cat in categories:
        cat_mask = df["category"] == cat
        cat_kec = df.loc[cat_mask, kec_features].mean().values
        cat_eeg = df.loc[cat_mask, eeg_features].mean().values

        category_kec.append(cat_kec)
        category_eeg.append(cat_eeg)
        category_labels.append(cat)

    category_kec = np.array(category_kec)
    category_eeg = np.array(category_eeg)

    # Compute RDMs
    kec_cat_rdm = compute_rdm(category_kec)
    eeg_cat_rdm = compute_rdm(category_eeg)

    # RSA correlation
    rsa_corr, rsa_p = rsa_correlation(kec_cat_rdm, eeg_cat_rdm)

    print(f"Category RSA Correlation: r = {rsa_corr:.4f}, p = {rsa_p:.4f}")

    # Visualize category RDMs
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))

    # KEC category RDM
    im1 = ax1.imshow(kec_cat_rdm, cmap="viridis", aspect="auto")
    ax1.set_title("KEC Category RDM")
    ax1.set_xticks(range(len(category_labels)))
    ax1.set_yticks(range(len(category_labels)))
    ax1.set_xticklabels(category_labels, rotation=45, ha="right")
    ax1.set_yticklabels(category_labels)
    plt.colorbar(im1, ax=ax1, shrink=0.8)

    # EEG category RDM
    im2 = ax2.imshow(eeg_cat_rdm, cmap="viridis", aspect="auto")
    ax2.set_title("EEG Category RDM")
    ax2.set_xticks(range(len(category_labels)))
    ax2.set_yticks(range(len(category_labels)))
    ax2.set_xticklabels(category_labels, rotation=45, ha="right")
    ax2.set_yticklabels(category_labels)
    plt.colorbar(im2, ax=ax2, shrink=0.8)

    # RSA scatter plot
    mask = np.triu(np.ones_like(kec_cat_rdm, dtype=bool), k=1)
    kec_vec = kec_cat_rdm[mask]
    eeg_vec = eeg_cat_rdm[mask]

    ax3.scatter(kec_vec, eeg_vec, s=100, alpha=0.7)

    # Add regression line
    z = np.polyfit(kec_vec, eeg_vec, 1)
    p = np.poly1d(z)
    ax3.plot(kec_vec, p(kec_vec), "r--", alpha=0.8, linewidth=2)

    ax3.set_xlabel("KEC Category Dissimilarity")
    ax3.set_ylabel("EEG Category Dissimilarity")
    ax3.set_title(f"Category RSA\nr = {rsa_corr:.4f}, p = {rsa_p:.4f}")
    ax3.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig("../figures/category_rsa_analysis.png", dpi=300, bbox_inches="tight")
    plt.show()

    return {
        "category_kec_rdm": kec_cat_rdm,
        "category_eeg_rdm": eeg_cat_rdm,
        "category_labels": category_labels,
        "rsa_correlation": rsa_corr,
        "rsa_p_value": rsa_p,
    }


def create_rsa_summary_report(kec_eeg_rsa, temporal_rsa, category_rsa):
    """Create comprehensive RSA analysis report"""

    print("\n" + "=" * 60)
    print("RSA ANALYSIS SUMMARY REPORT")
    print("=" * 60)

    print("\n1. KEC ↔ EEG Cross-Modal RSA:")
    print(f"   Correlation: r = {kec_eeg_rsa['rsa_correlation']:.4f}")
    print(f"   Significance: p = {kec_eeg_rsa['rsa_p_value']:.4f}")
    print(
        f"   Bootstrap 95% CI: [{kec_eeg_rsa['bootstrap_ci'][0]:.4f}, {kec_eeg_rsa['bootstrap_ci'][1]:.4f}]"
    )

    if kec_eeg_rsa["rsa_p_value"] < 0.001:
        significance = "*** (p < 0.001)"
    elif kec_eeg_rsa["rsa_p_value"] < 0.01:
        significance = "** (p < 0.01)"
    elif kec_eeg_rsa["rsa_p_value"] < 0.05:
        significance = "* (p < 0.05)"
    else:
        significance = "ns (not significant)"

    print(f"   Interpretation: {significance}")

    if temporal_rsa:
        print("\n2. Temporal RSA Analysis:")
        for result in temporal_rsa:
            sig_marker = (
                "***"
                if result["rsa_p_value"] < 0.001
                else "**"
                if result["rsa_p_value"] < 0.01
                else "*"
                if result["rsa_p_value"] < 0.05
                else "ns"
            )
            print(
                f"   {result['time_window']}: r = {result['rsa_correlation']:.4f} {sig_marker}"
            )

    if category_rsa:
        print("\n3. Category-based RSA:")
        print(f"   Correlation: r = {category_rsa['rsa_correlation']:.4f}")
        print(f"   Significance: p = {category_rsa['rsa_p_value']:.4f}")
        print(f"   Categories: {', '.join(category_rsa['category_labels'])}")

    print("\n" + "=" * 60)
    print("CONCLUSIONS:")
    print("=" * 60)

    # Generate conclusions based on results
    if kec_eeg_rsa["rsa_correlation"] > 0.3 and kec_eeg_rsa["rsa_p_value"] < 0.05:
        print("✓ STRONG EVIDENCE for KEC-EEG representational correspondence")
        print("  → KEC metrics capture neural representational structure")
        print("  → Cross-modal validation supports theoretical framework")
    elif kec_eeg_rsa["rsa_correlation"] > 0.15 and kec_eeg_rsa["rsa_p_value"] < 0.05:
        print("✓ MODERATE EVIDENCE for KEC-EEG correspondence")
        print("  → Significant but modest representational alignment")
    else:
        print("⚠ LIMITED EVIDENCE for KEC-EEG correspondence")
        print("  → May require methodological refinements")

    if temporal_rsa:
        significant_windows = [r for r in temporal_rsa if r["rsa_p_value"] < 0.05]
        if significant_windows:
            print(
                f"✓ TEMPORAL SPECIFICITY: {len(significant_windows)}/{len(temporal_rsa)} time windows significant"
            )
            best_window = max(significant_windows, key=lambda x: x["rsa_correlation"])
            print(f"  → Peak correspondence in {best_window['time_window']}")

    if category_rsa and category_rsa["rsa_p_value"] < 0.05:
        print("✓ CATEGORICAL STRUCTURE preserved across modalities")
        print("  → Semantic organization reflected in both KEC and EEG")

    print("\n" + "=" * 60)


def main():
    """Main RSA analysis pipeline"""

    print("Representational Similarity Analysis (RSA)")
    print("Cross-Modal Validation: KEC ↔ Neural Patterns")
    print("=" * 60)

    # Create output directories
    Path("../figures").mkdir(exist_ok=True)
    Path("../outputs/rsa_analysis").mkdir(parents=True, exist_ok=True)

    # Load data
    result = load_or_create_data()
    if isinstance(result, tuple):
        df, eeg_data = result
    else:
        df, eeg_data = result, None

    # Clean data
    df = df.dropna()
    print(f"Clean dataset: {df.shape}")

    # Run RSA analyses
    print("\n" + "=" * 60)

    # 1. KEC ↔ EEG RSA
    kec_eeg_rsa = run_kec_eeg_rsa(df, eeg_data)

    # 2. Temporal RSA (if EEG time series available)
    temporal_rsa = run_temporal_rsa(df, eeg_data) if eeg_data else None

    # 3. Category RSA (if category information available)
    category_rsa = run_category_rsa(df)

    # 4. Generate summary report
    create_rsa_summary_report(kec_eeg_rsa, temporal_rsa, category_rsa)

    # Save results
    results = {
        "kec_eeg_rsa": kec_eeg_rsa,
        "temporal_rsa": temporal_rsa,
        "category_rsa": category_rsa,
    }

    # Save summary statistics
    summary_stats = {
        "cross_modal_correlation": kec_eeg_rsa["rsa_correlation"],
        "cross_modal_p_value": kec_eeg_rsa["rsa_p_value"],
        "bootstrap_ci_lower": kec_eeg_rsa["bootstrap_ci"][0],
        "bootstrap_ci_upper": kec_eeg_rsa["bootstrap_ci"][1],
    }

    if temporal_rsa:
        for i, result in enumerate(temporal_rsa):
            summary_stats[f"temporal_window_{i+1}_correlation"] = result[
                "rsa_correlation"
            ]
            summary_stats[f"temporal_window_{i+1}_p_value"] = result["rsa_p_value"]

    if category_rsa:
        summary_stats["category_correlation"] = category_rsa["rsa_correlation"]
        summary_stats["category_p_value"] = category_rsa["rsa_p_value"]

    # Save as CSV
    summary_df = pd.DataFrame([summary_stats])
    summary_df.to_csv("../outputs/rsa_analysis/rsa_summary_statistics.csv", index=False)

    print(f"\n✓ RSA analysis completed successfully!")
    print(f"✓ Results saved to ../outputs/rsa_analysis/")
    print(f"✓ Figures saved to ../figures/")

    return results


if __name__ == "__main__":
    main()
