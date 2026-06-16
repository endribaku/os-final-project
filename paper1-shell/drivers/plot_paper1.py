#!/usr/bin/env python3
"""
drivers/plot_paper1.py
----------------------
Generate all figures for Paper 1 from the benchmark CSVs in results/.

Figures produced (all PNG, 300 dpi):
    figures/orig_vs_opt_wall_time.png   -- side-by-side bar chart, all 10 scripts
    figures/orig_vs_opt_cpu.png         -- same for CPU %
    figures/orig_vs_opt_rss.png         -- peak RSS
    figures/<script>_wall_by_input.png  -- per-script: wall time by input size
    figures/crt_comparison.png          -- brute vs CRT wall time
    figures/logscout_scaling.png        -- logscout wall time vs log lines

Usage (from repo root):
    python3 paper1-shell/drivers/plot_paper1.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from common import plots  # applies shared style on import

RESULTS = REPO_ROOT / "paper1-shell" / "results"
FIGURES = REPO_ROOT / "paper1-shell" / "figures"
FIGURES.mkdir(parents=True, exist_ok=True)

SCRIPTS = [
    "mailformat", "rn", "blank-rename", "encryptedpw", "collatz",
    "days-between", "game_of_life", "primes", "makedict", "tree",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load(name: str, variant: str) -> pd.DataFrame | None:
    p = RESULTS / f"{name}_{variant}.csv"
    if not p.exists():
        return None
    df = pd.read_csv(p)
    df["script"]  = name
    df["variant"] = variant
    return df


def summary(df: pd.DataFrame, col: str) -> tuple[float, float]:
    """Return (mean, std) of `col` across all rows."""
    vals = df[col].dropna()
    return float(vals.mean()), float(vals.std())


# ---------------------------------------------------------------------------
# 1. Side-by-side bar: original vs optimised, all 10 scripts
# ---------------------------------------------------------------------------

def plot_global_comparison() -> None:
    metrics = {
        "wall_time_s": ("Wall-clock time (s)", "orig_vs_opt_wall_time.png"),
        "cpu_pct":     ("CPU usage (%)",        "orig_vs_opt_cpu.png"),
        "max_rss_kb":  ("Peak RSS (KB)",         "orig_vs_opt_rss.png"),
    }

    for col, (ylabel, fname) in metrics.items():
        orig_means, orig_stds = [], []
        opt_means,  opt_stds  = [], []
        labels = []

        for s in SCRIPTS:
            df_o = load(s, "original")
            df_p = load(s, "optimized")
            if df_o is None or df_p is None:
                continue
            labels.append(s.replace("-", "\n").replace("_", "\n"))
            m, sd = summary(df_o, col); orig_means.append(m); orig_stds.append(sd)
            m, sd = summary(df_p, col); opt_means.append(m);  opt_stds.append(sd)

        if not labels:
            print(f"  skip {fname} — no data"); continue

        fig, ax = plots.bar_compare(
            groups=labels,
            series={
                "Original":  orig_means,
                "Optimized": opt_means,
            },
            errors={
                "Original":  orig_stds,
                "Optimized": opt_stds,
            },
            ylabel=ylabel,
            title=f"Original vs Optimized — {ylabel}",
        )
        ax.set_xticklabels(labels, fontsize=7)
        plots.save(fig, FIGURES / fname)
        print(f"  saved {fname}")


# ---------------------------------------------------------------------------
# 2. Per-script wall time by input size
# ---------------------------------------------------------------------------

def plot_per_script() -> None:
    for s in SCRIPTS:
        df_o = load(s, "original")
        df_p = load(s, "optimized")
        if df_o is None or df_p is None:
            continue

        # Group by the 'cmd' label which encodes input size
        frames = {"Original": df_o, "Optimized": df_p}
        fig, ax = plt.subplots()
        ax.set_title(f"{s} — wall time by input", fontsize=10)
        ax.set_ylabel("Wall-clock time (s)")
        ax.set_xlabel("Input case")

        for variant, df in frames.items():
            grouped = df.groupby("cmd")["wall_time_s"]
            labels  = [k.split(":")[-1] for k in grouped.groups.keys()]
            means   = [grouped.get_group(k).mean() for k in grouped.groups]
            stds    = [grouped.get_group(k).std()  for k in grouped.groups]
            x = np.arange(len(labels))
            offset = -0.2 if variant == "Original" else 0.2
            ax.bar(x + offset, means, 0.35, yerr=stds, label=variant,
                   capsize=4, alpha=0.85)

        ax.set_xticks(np.arange(len(labels)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
        ax.legend()
        ax.grid(axis="y", alpha=0.3)

        fname = f"{s}_wall_by_input.png"
        plots.save(fig, FIGURES / fname)
        print(f"  saved {fname}")


# ---------------------------------------------------------------------------
# 3. CRT comparison
# ---------------------------------------------------------------------------

def plot_crt() -> None:
    p = RESULTS / "crt_comparison.csv"
    if not p.exists():
        print("  skip crt_comparison.png — no data"); return

    df = pd.read_csv(p)
    grouped = df.groupby("variant")["wall_time_s"]
    variants = list(grouped.groups.keys())
    means = [grouped.get_group(v).mean() for v in variants]
    stds  = [grouped.get_group(v).std()  for v in variants]

    fig, ax = plt.subplots()
    ax.bar(variants, means, yerr=stds, capsize=6, color=["#e07b54", "#5b8db8"],
           alpha=0.85)
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("CRT Case Study: Brute Force vs Chinese Remainder Theorem")
    ax.grid(axis="y", alpha=0.3)
    plots.save(fig, FIGURES / "crt_comparison.png")
    print("  saved crt_comparison.png")


# ---------------------------------------------------------------------------
# 4. logscout scaling
# ---------------------------------------------------------------------------

def plot_logscout() -> None:
    p = RESULTS / "logscout_newtool.csv"
    if not p.exists():
        print("  skip logscout_scaling.png — no data"); return

    df = pd.read_csv(p)
    # cmd encodes "logscout:lines<N>"
    df["n_lines"] = df["cmd"].str.extract(r"lines(\d+)").astype(int)
    grouped = df.groupby("n_lines")["wall_time_s"]
    x = sorted(grouped.groups.keys())
    means = [grouped.get_group(n).mean() for n in x]
    stds  = [grouped.get_group(n).std()  for n in x]

    fig, ax = plt.subplots()
    ax.errorbar(x, means, yerr=stds, marker="o", capsize=4)
    ax.set_xscale("log")
    ax.set_xlabel("Log lines")
    ax.set_ylabel("Wall-clock time (s)")
    ax.set_title("logscout — scaling with log file size")
    plots.save(fig, FIGURES / "logscout_scaling.png")
    print("  saved logscout_scaling.png")


# ---------------------------------------------------------------------------

def main() -> None:
    print("Generating Paper 1 figures...\n")
    plot_global_comparison()
    plot_per_script()
    plot_crt()
    plot_logscout()
    print(f"\nAll figures written to {FIGURES}")


if __name__ == "__main__":
    main()
