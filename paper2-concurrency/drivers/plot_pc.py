#!/usr/bin/env python3
"""
Plot Producer-Consumer sweep results.

Reads `paper2-concurrency/results/pc_sweep.csv` (produced by sweep_pc.py)
and writes the figures Paper 2 needs into
`paper2-concurrency/figures/pc/`.

Figures produced (impl is always the line / colour dimension):
    throughput_vs_N.png        throughput        vs buffer size N
    walltime_vs_M.png          wall time         vs producer count M
    walltime_vs_K.png          wall time         vs consumer count K
    cpu_vs_contention.png      CPU%              vs total workers (M+K)
    latency_p95_vs_N.png       p95 latency       vs buffer size N
    ctxsw_vs_threads.png       total ctx switches vs (M+K)
    rss_vs_N.png               max RSS           vs buffer size N
    impl_bar_comparison.png    3-panel bar comparison at the median config

Usage:
    PYTHONPATH=. python paper2-concurrency/drivers/plot_pc.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _plot_common import (  # noqa: E402
    grouped_barplot_panel, grouped_lineplot, load_or_die, median_of,
)

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_IN  = ROOT / "paper2-concurrency/results/pc_sweep.csv"
DEFAULT_OUT = ROOT / "paper2-concurrency/figures/pc"


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

    # Median values along each axis are used to fix the other axes when
    # drawing a one-dimensional sweep. (Picks a single "central" slice.)
    N_mid = median_of(df["N"])
    M_mid = median_of(df["M"])
    K_mid = median_of(df["K"])

    # 1) throughput vs N    (M, K fixed)
    sub = df[(df["M"] == M_mid) & (df["K"] == K_mid)]
    grouped_lineplot(
        sub, x_col="N", y_col="throughput_per_sec",
        xlabel=f"Buffer size N    (M={M_mid}, K={K_mid})",
        ylabel="Throughput (items / sec)",
        title="Throughput vs buffer size",
        out=out_path / "throughput_vs_N.png",
        logx=True,
    )

    # 2) wall time vs M     (N, K fixed)
    sub = df[(df["N"] == N_mid) & (df["K"] == K_mid)]
    grouped_lineplot(
        sub, x_col="M", y_col="wall_time_s",
        xlabel=f"Producers M    (N={N_mid}, K={K_mid})",
        ylabel="Wall time (s)",
        title="Wall time vs producer count",
        out=out_path / "walltime_vs_M.png",
    )

    # 3) wall time vs K     (N, M fixed)
    sub = df[(df["N"] == N_mid) & (df["M"] == M_mid)]
    grouped_lineplot(
        sub, x_col="K", y_col="wall_time_s",
        xlabel=f"Consumers K    (N={N_mid}, M={M_mid})",
        ylabel="Wall time (s)",
        title="Wall time vs consumer count",
        out=out_path / "walltime_vs_K.png",
    )

    # 4) CPU % vs total workers (M+K)
    df2 = df.assign(threads=df["M"] + df["K"])
    sub = df2[df2["N"] == N_mid]
    grouped_lineplot(
        sub, x_col="threads", y_col="cpu_pct",
        xlabel=f"Total worker threads M+K    (N={N_mid})",
        ylabel="CPU usage (%)",
        title="CPU vs contention",
        out=out_path / "cpu_vs_contention.png",
    )

    # 5) p95 latency vs N
    sub = df[(df["M"] == M_mid) & (df["K"] == K_mid)]
    grouped_lineplot(
        sub, x_col="N", y_col="latency_p95_us",
        xlabel=f"Buffer size N    (M={M_mid}, K={K_mid})",
        ylabel="p95 end-to-end latency (μs)",
        title="p95 latency vs buffer size",
        out=out_path / "latency_p95_vs_N.png",
        logx=True, logy=True,
    )

    # 6) Context switches vs threads
    df3 = df2.assign(ctxsw=df2["voluntary_ctx"] + df2["involuntary_ctx"])
    sub = df3[df3["N"] == N_mid]
    grouped_lineplot(
        sub, x_col="threads", y_col="ctxsw",
        xlabel=f"Total worker threads M+K    (N={N_mid})",
        ylabel="Total context switches",
        title="Context switches vs thread count",
        out=out_path / "ctxsw_vs_threads.png",
    )

    # 7) Max RSS vs N
    sub = df[(df["M"] == M_mid) & (df["K"] == K_mid)]
    grouped_lineplot(
        sub, x_col="N", y_col="max_rss_kb",
        xlabel=f"Buffer size N    (M={M_mid}, K={K_mid})",
        ylabel="Max RSS (kB)",
        title="Peak memory vs buffer size",
        out=out_path / "rss_vs_N.png",
        logx=True,
    )

    # 8) 3-panel bar comparison at the median (N, M, K)
    ref = df[(df["N"] == N_mid) & (df["M"] == M_mid) & (df["K"] == K_mid)]
    if not ref.empty:
        grouped_barplot_panel(
            ref,
            metrics=[
                ("throughput_per_sec", "Throughput (items/sec)"),
                ("latency_mean_us",    "Mean latency (μs)"),
                ("cpu_pct",            "CPU usage (%)"),
            ],
            suptitle=f"Reference comparison    (N={N_mid}, M={M_mid}, K={K_mid})",
            out=out_path / "impl_bar_comparison.png",
        )

    print(f"[plot_pc] figures -> {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
