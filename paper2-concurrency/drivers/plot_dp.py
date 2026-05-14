#!/usr/bin/env python3
"""
Plot Dining Philosophers sweep results.

Reads `paper2-concurrency/results/dp_sweep.csv` (produced by sweep_dp.py)
and writes the figures Paper 2 needs into
`paper2-concurrency/figures/dp/`.

Figures produced (impl is always the line / colour dimension):
    meals_vs_P.png             total meals       vs P philosophers
    wait_p95_vs_P.png          p95 wait latency  vs P
    cpu_vs_P.png               CPU%              vs P
    ctxsw_vs_P.png             ctx switches      vs P
    rss_vs_P.png               max RSS           vs P
    fairness_vs_P.png          std(meals per phil) vs P (lower = fairer)
    deadlock_freq_vs_P.png     fraction of runs that deadlocked (per impl, per P)
    impl_bar_comparison.png    3-panel bar comparison at the median P

Usage:
    PYTHONPATH=. python paper2-concurrency/drivers/plot_dp.py
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _plot_common import (  # noqa: E402
    color_for, grouped_barplot_panel, grouped_lineplot, label_for,
    load_or_die, median_of,
)
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from common import plots  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN  = ROOT / "paper2-concurrency/results/dp_sweep.csv"
DEFAULT_OUT = ROOT / "paper2-concurrency/figures/dp"


def _meals_std(meals_per_phil_str: str) -> float:
    """Parse the meals_per_phil CSV field (a stringified list) and return std-dev."""
    try:
        arr = ast.literal_eval(meals_per_phil_str)
        return float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    except Exception:
        return float("nan")


def _deadlock_freq_plot(df: pd.DataFrame, out: Path) -> None:
    """Grouped bar plot: fraction of runs with deadlocked=True, per (impl, P)."""
    if "deadlocked" not in df.columns:
        return
    # deadlocked may be bool or string "true"/"false" depending on CSV
    d = df.copy()
    d["deadlocked"] = d["deadlocked"].apply(
        lambda v: bool(v) if isinstance(v, (bool, np.bool_)) else str(v).lower() == "true"
    )
    agg = (
        d.groupby(["impl", "N"])["deadlocked"]
         .mean()
         .reset_index()
         .rename(columns={"deadlocked": "deadlock_rate"})
    )
    if agg["deadlock_rate"].sum() == 0:
        # nothing deadlocked -- still emit a (mostly empty) chart so it's
        # explicit that no variants deadlocked under the chosen params.
        pass

    impls = sorted(agg["impl"].unique())
    Ps    = sorted(agg["N"].unique())
    fig, ax = plt.subplots(figsize=(max(6.5, 0.6 * len(Ps) * len(impls)), 4.0))
    width = 0.8 / max(len(impls), 1)
    x = np.arange(len(Ps))
    for i, impl in enumerate(impls):
        rates = [
            float(agg[(agg["impl"] == impl) & (agg["N"] == P)]["deadlock_rate"].mean()
                  if not agg[(agg["impl"] == impl) & (agg["N"] == P)].empty else 0.0)
            for P in Ps
        ]
        ax.bar(x + i * width - 0.4 + width / 2, rates, width,
               label=label_for(impl), color=color_for(impl))
    ax.set_xticks(x)
    ax.set_xticklabels([str(P) for P in Ps])
    ax.set_xlabel("Philosophers P")
    ax.set_ylabel("Fraction of runs deadlocked")
    ax.set_ylim(0, 1.05)
    ax.set_title("Deadlock frequency vs P")
    ax.legend()
    plots.save(fig, out)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--in",  dest="inp", type=str, default=str(DEFAULT_IN))
    ap.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    args = ap.parse_args()

    in_path  = Path(args.inp)
    out_path = Path(args.out)
    out_path.mkdir(parents=True, exist_ok=True)

    df = load_or_die(in_path)

    # In the DP CSV, "N" is the number of philosophers (the JSON field).
    P_mid = median_of(df["N"])

    # Derived columns
    df = df.assign(
        ctxsw          = df["voluntary_ctx"] + df["involuntary_ctx"],
        meals_phil_std = df["meals_per_phil"].apply(_meals_std),
    )

    # 1) total meals vs P
    grouped_lineplot(
        df, x_col="N", y_col="total_meals",
        xlabel="Philosophers P",
        ylabel="Total meals (across all philosophers)",
        title="Throughput (meals) vs P",
        out=out_path / "meals_vs_P.png",
    )

    # 2) p95 wait latency vs P
    grouped_lineplot(
        df, x_col="N", y_col="wait_p95_us",
        xlabel="Philosophers P",
        ylabel="p95 wait latency (μs)",
        title="p95 wait latency vs P",
        out=out_path / "wait_p95_vs_P.png",
        logy=True,
    )

    # 3) CPU % vs P
    grouped_lineplot(
        df, x_col="N", y_col="cpu_pct",
        xlabel="Philosophers P",
        ylabel="CPU usage (%)",
        title="CPU vs P",
        out=out_path / "cpu_vs_P.png",
    )

    # 4) Context switches vs P
    grouped_lineplot(
        df, x_col="N", y_col="ctxsw",
        xlabel="Philosophers P",
        ylabel="Total context switches",
        title="Context switches vs P",
        out=out_path / "ctxsw_vs_P.png",
    )

    # 5) Max RSS vs P
    grouped_lineplot(
        df, x_col="N", y_col="max_rss_kb",
        xlabel="Philosophers P",
        ylabel="Max RSS (kB)",
        title="Peak memory vs P",
        out=out_path / "rss_vs_P.png",
    )

    # 6) Fairness: std-dev of meals_per_phil vs P (lower = fairer)
    grouped_lineplot(
        df, x_col="N", y_col="meals_phil_std",
        xlabel="Philosophers P",
        ylabel="Std. dev. of meals per philosopher",
        title="Fairness across philosophers (lower is fairer)",
        out=out_path / "fairness_vs_P.png",
    )

    # 7) Deadlock frequency
    _deadlock_freq_plot(df, out_path / "deadlock_freq_vs_P.png")

    # 8) 3-panel bar comparison at median P
    ref = df[df["N"] == P_mid]
    if not ref.empty:
        grouped_barplot_panel(
            ref,
            metrics=[
                ("total_meals",    "Total meals"),
                ("wait_p95_us",    "p95 wait (μs)"),
                ("cpu_pct",        "CPU usage (%)"),
            ],
            suptitle=f"Reference comparison    (P={P_mid})",
            out=out_path / "impl_bar_comparison.png",
        )

    print(f"[plot_dp] figures -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
