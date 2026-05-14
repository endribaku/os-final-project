"""
Shared plotting helpers for the Paper 2 plot scripts (plot_pc.py, plot_dp.py).

Keeps a single source of truth for:
  - palette / label maps per `impl` so every figure colours implementations
    the same way and uses friendly names in legends;
  - a grouped-lineplot-with-errorbars helper that operates on a long-form
    pandas DataFrame (mean ± std across reps/seeds per x value);
  - a grouped-bar-comparison helper for "metric at a fixed config" figures.

Depends on:  pandas, numpy, matplotlib (and our common.plots styling).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import plots  # noqa: E402 -- sets matplotlib rc

IMPL_LABEL: dict[str, str] = {
    "java-monitor":         "Java monitor",
    "java-lockfree":        "Java lock-free MPMC",
    "java-semaphore":       "Java semaphore",
    "java-hierarchy":       "Java hierarchy",
    "c-pthreads-sem":       "C pthreads (mutex+2sem)",
    "c-pthreads-monitor":   "C pthreads monitor",
    "c-pthreads-hierarchy": "C pthreads hierarchy",
    "c-pthreads-naive":     "C pthreads naive",
}

IMPL_COLOR: dict[str, str] = {
    "java-monitor":         "#1f77b4",
    "java-lockfree":        "#2ca02c",
    "java-semaphore":       "#17becf",
    "java-hierarchy":       "#9467bd",
    "c-pthreads-sem":       "#ff7f0e",
    "c-pthreads-monitor":   "#d62728",
    "c-pthreads-hierarchy": "#8c564b",
    "c-pthreads-naive":     "#e377c2",
}


def label_for(impl: str) -> str:
    return IMPL_LABEL.get(impl, impl)


def color_for(impl: str) -> str:
    return IMPL_COLOR.get(impl, "gray")


def grouped_lineplot(
    df: pd.DataFrame,
    *,
    x_col: str,
    y_col: str,
    group_col: str = "impl",
    xlabel: str = "",
    ylabel: str = "",
    title: str = "",
    out: Path,
    logx: bool = False,
    logy: bool = False,
) -> None:
    """
    One line per group_col, mean ± std across rows at each x.

    Different groups may have different numbers of samples per x — we use
    pandas `groupby` so it doesn't matter.
    """
    fig, ax = plt.subplots()
    for impl, sub in df.groupby(group_col):
        agg = (
            sub.groupby(x_col)[y_col]
               .agg(["mean", "std", "count"])
               .reset_index()
               .sort_values(x_col)
        )
        agg["std"] = agg["std"].fillna(0.0)
        ax.errorbar(
            agg[x_col], agg["mean"], yerr=agg["std"],
            marker="o", capsize=3,
            label=label_for(impl), color=color_for(impl),
        )
    if logx: ax.set_xscale("log")
    if logy: ax.set_yscale("log")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ax.has_data():
        ax.legend()
    plots.save(fig, out)
    plt.close(fig)


def grouped_barplot_panel(
    df: pd.DataFrame,
    *,
    metrics: Iterable[tuple[str, str]],   # [(column, panel_title), ...]
    group_col: str = "impl",
    suptitle: str = "",
    out: Path,
) -> None:
    """
    Side-by-side bar panels at a fixed config. Each panel shows one metric
    with one bar per implementation (mean ± std).
    """
    metrics = list(metrics)
    n = len(metrics)
    if n == 0:
        return
    fig, axes = plt.subplots(1, n, figsize=(4.0 * n, 4.0))
    if n == 1:
        axes = [axes]

    impls = sorted(df[group_col].unique())
    x = np.arange(len(impls))

    for ax, (col, panel_title) in zip(axes, metrics):
        means = [df[df[group_col] == i][col].mean() for i in impls]
        stds  = [df[df[group_col] == i][col].std(ddof=1)
                 if (df[group_col] == i).sum() > 1 else 0.0
                 for i in impls]
        ax.bar(x, means, yerr=stds, capsize=4,
               color=[color_for(i) for i in impls])
        ax.set_xticks(x)
        ax.set_xticklabels([label_for(i) for i in impls], rotation=25, ha="right")
        ax.set_title(panel_title)
        ax.set_ylabel(panel_title)
    if suptitle:
        fig.suptitle(suptitle)
    plots.save(fig, out)
    plt.close(fig)


def load_or_die(csv_path: Path) -> pd.DataFrame:
    if not csv_path.exists():
        sys.exit(f"input CSV not found: {csv_path}\n"
                 f"  (run the sweep driver first)")
    df = pd.read_csv(csv_path)
    if df.empty:
        sys.exit(f"input CSV is empty: {csv_path}")
    print(f"[plot] loaded {len(df)} rows from {csv_path}", file=sys.stderr)
    return df


def median_of(values) -> object:
    """Median element of a uniques iterable (used to pick a reference config)."""
    arr = sorted(set(values))
    return arr[len(arr) // 2]
