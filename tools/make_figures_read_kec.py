#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
PROC = ROOT / 'data' / 'processed'
FIG  = ROOT / 'figures' / 'metrics'
FIG.mkdir(parents=True, exist_ok=True)

def save_multi(path_png: Path, fig):
    path_png.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path_png, dpi=180, bbox_inches='tight')
    fig.savefig(path_png.with_suffix('.pdf'), bbox_inches='tight')
    fig.savefig(path_png.with_suffix('.svg'), bbox_inches='tight')

def style_axes(ax, title: str, xlabel: str, ylabel: str):
    ax.grid(True, axis='both', linestyle='--', alpha=0.35, zorder=0)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

def main() -> int:
    merged = PROC / 'zuco_kec_merged.csv'
    if not merged.exists():
        print('[warn] missing', merged)
        return 0
    df = pd.read_csv(merged)
    # aggregate to sentence-level where possible
    keys = [k for k in ['Subject','SentenceID'] if k in df.columns]
    keep = {c: (c, 'mean') for c in ['TRT','theta1','alpha1','z_kec'] if c in df.columns}
    if keys:
        agg = df.groupby(keys, dropna=False).agg(**keep)
        agg.columns = agg.columns.get_level_values(0)
        ds = agg.reset_index()
    else:
        ds = df.copy()

    # F2 — Reading vs KEC
    if {'TRT','z_kec'}.issubset(ds.columns):
        x = ds['z_kec'].astype(float)
        y = ds['TRT'].astype(float)
        fig, ax = plt.subplots(figsize=(6,4))
        ax.scatter(x, y, s=10, alpha=0.55, color='#1f77b4', edgecolor='none', zorder=2)
        r2_txt = ''
        if len(x) > 1:
            xm, ym = np.nanmean(x), np.nanmean(y)
            coef = np.polyfit(x.fillna(xm), y.fillna(ym), 1)
            xx = np.linspace(np.nanmin(x), np.nanmax(x), 100)
            yy = coef[0]*xx + coef[1]
            ax.plot(xx, yy, color='#ff7f0e', linewidth=1.5, zorder=3)
            yhat = coef[0]*x + coef[1]
            ss_res = np.nansum((y - yhat)**2)
            ss_tot = np.nansum((y - np.nanmean(y))**2)
            r2 = 1 - ss_res/ss_tot if ss_tot != 0 else 0.0
            r2_txt = f'  (R²={r2:.2f})'
        style_axes(ax, f'Reading vs KEC{r2_txt}', 'z(KEC)', 'Sentence-level TRT (mean)')
        fig.tight_layout(); save_multi(FIG/'F2_reading_vs_KEC.png', fig); plt.close(fig)
    else:
        print('[note] F2 skipped — columns not found in merged data')

    # F3 — EEG bands vs KEC
    have = [c for c in ['theta1','alpha1'] if c in ds.columns]
    if 'z_kec' in ds.columns and have:
        fig = plt.figure(figsize=(8,4))
        bands = [('theta1','Theta'), ('alpha1','Alpha')]
        for i, (col, title) in enumerate(bands, start=1):
            ax = plt.subplot(1,2,i)
            if col in ds.columns and ds[col].notna().any():
                x = ds['z_kec'].astype(float); y = ds[col].astype(float)
                ax.scatter(x, y, s=10, alpha=0.55, color='#1f77b4', edgecolor='none', zorder=2)
                r2_txt = ''
                if len(x) > 1:
                    xm, ym = np.nanmean(x), np.nanmean(y)
                    coef = np.polyfit(x.fillna(xm), y.fillna(ym), 1)
                    xx = np.linspace(np.nanmin(x), np.nanmax(x), 100)
                    yy = coef[0]*xx + coef[1]
                    ax.plot(xx, yy, color='#ff7f0e', linewidth=1.5, zorder=3)
                    yhat = coef[0]*x + coef[1]
                    ss_res = np.nansum((y - yhat)**2)
                    ss_tot = np.nansum((y - np.nanmean(y))**2)
                    r2 = 1 - ss_res/ss_tot if ss_tot != 0 else 0.0
                    r2_txt = f'  (R²={r2:.2f})'
                style_axes(ax, f'{title} vs KEC{r2_txt}', 'z(KEC)', f'Sentence-level {title}')
            else:
                ax.text(0.5, 0.5, f'No {title} data', ha='center', va='center')
                ax.set_axis_off()
        fig.tight_layout(); save_multi(FIG/'F3_EEG_vs_KEC.png', fig); plt.close(fig)
    else:
        print('[note] F3 skipped — columns not found in merged data')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

