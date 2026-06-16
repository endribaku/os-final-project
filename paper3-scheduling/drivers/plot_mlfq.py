"""
drivers/plot_mlfq.py
Visualise the MLFQ grid search (Paper 3 §7): heatmaps + 2D + 3D surfaces.

Reads paper3-scheduling/results/mlfq_<variant>.csv (produced by run_mlfq.py)
and writes figures to paper3-scheduling/figures/mlfq/.

For each metric it draws a Q1 x Q2 heatmap and a 3D performance surface, taking
the (L1, L2) slice that is optimal for that metric so the figure shows the best
achievable behaviour. A line plot of each metric vs Q1 is also produced.

Usage
-----
    python paper3-scheduling/drivers/plot_mlfq.py --variant A
"""
from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict

from _p3_common import FIGURES_DIR, RESULTS_DIR

from common.plots import heatmap, line_with_errorbars, save, surface3d
import numpy as np

# metric -> (human label, optimization direction)
METRICS = {
    "throughput":      ("Throughput (jobs/time-unit)", "max"),
    "turnaround_mean": ("Mean turnaround time",        "min"),
    "waiting_mean":    ("Mean waiting time",           "min"),
    "response_mean":   ("Mean response time",          "min"),
}


def load_rows(path) -> list[dict]:
    with open(path) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k, v in list(r.items()):
            try:
                r[k] = float(v)
            except (ValueError, TypeError):
                pass
    return rows


def best_slice(rows: list[dict], metric: str, direction: str) -> tuple[float, float]:
    """Return the (L1, L2) pair whose best cell is globally optimal."""
    pick = max if direction == "max" else min
    row = pick(rows, key=lambda r: r[metric])
    return row["L1"], row["L2"]


def grid_matrix(rows: list[dict], metric: str, l1: float, l2: float):
    """Build a Q1 x Q2 value matrix for the fixed (L1, L2) slice."""
    sliced = [r for r in rows if r["L1"] == l1 and r["L2"] == l2]
    q1s = sorted({r["Q1"] for r in sliced})
    q2s = sorted({r["Q2"] for r in sliced})
    lookup = {(r["Q1"], r["Q2"]): r[metric] for r in sliced}
    M = np.array([[lookup.get((q1, q2), np.nan) for q1 in q1s] for q2 in q2s])
    return M, q1s, q2s


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Plot the MLFQ grid search.")
    ap.add_argument("--variant", choices=["A", "B"], default="A")
    args = ap.parse_args(argv)

    src = RESULTS_DIR / f"mlfq_{args.variant}.csv"
    if not src.exists():
        print(f"[plot_mlfq] missing {src}; run run_mlfq.py first", file=sys.stderr)
        return 1

    rows = load_rows(src)
    out = FIGURES_DIR / "mlfq"
    print(f"[plot_mlfq] {len(rows)} rows from {src.name} -> {out}/",
          file=sys.stderr)

    for metric, (label, direction) in METRICS.items():
        l1, l2 = best_slice(rows, metric, direction)
        M, q1s, q2s = grid_matrix(rows, metric, l1, l2)

        # Heatmap over the Q1 x Q2 grid.
        fig, _ = heatmap(
            M, xticks=q1s, yticks=q2s,
            xlabel="Q1 (level-0 quantum)", ylabel="Q2 (level-1 quantum)",
            title=f"{label}  (variant {args.variant}, L1={l1:.0f}, L2={l2:.0f})",
            cbar_label=label, annotate=True, annot_fmt="{:.1f}",
        )
        save(fig, out / f"heatmap_{metric}_{args.variant}.png")

        # 3D performance surface.
        X, Y = np.meshgrid(q1s, q2s)
        fig, _ = surface3d(
            X, Y, M,
            xlabel="Q1", ylabel="Q2", zlabel=label,
            title=f"{label} surface (variant {args.variant})",
        )
        save(fig, out / f"surface_{metric}_{args.variant}.png")

        # 2D line: metric vs Q1, one line per Q2 (best slice).
        sliced = [r for r in rows if r["L1"] == l1 and r["L2"] == l2]
        by_q2 = defaultdict(list)
        for r in sliced:
            by_q2[r["Q2"]].append((r["Q1"], r[metric]))
        fig = ax = None
        for q2 in sorted(by_q2):
            pts = sorted(by_q2[q2])
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            fig, ax = line_with_errorbars(
                xs, ys, label=f"Q2={q2:.0f}", ax=ax,
                xlabel="Q1 (level-0 quantum)", ylabel=label,
                title=f"{label} vs Q1 (variant {args.variant})",
            )
        if fig is not None:
            save(fig, out / f"line_{metric}_{args.variant}.png")

    print("[plot_mlfq] done.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
