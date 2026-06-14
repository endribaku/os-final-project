"""
drivers/plot_queuing.py
Visualise the queueing sweeps (Paper 3 §7, §9).

Reads paper3-scheduling/results/mq_analytic.csv (and mq_randomness.csv if it
exists) and writes figures to paper3-scheduling/figures/queuing/:

  - L, Lq, W, Wq and rho versus the server rate R, per model.
  - the same quantities versus the arrival load (N/M).
  - if the randomness study ran: a bar comparison of W and Wq across the
    exponential / uniform / poisson distributions.

Usage
-----
    python paper3-scheduling/drivers/plot_queuing.py
"""
from __future__ import annotations

import csv
import sys
from collections import defaultdict

from _p3_common import FIGURES_DIR, RESULTS_DIR

from common.plots import bar_compare, line_with_errorbars, save


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


def plot_vs_R(rows: list[dict], out) -> None:
    """Quantities vs server rate R, one line per model (M/M/1, M/M/S by s)."""
    # Pick a representative stable (N, M) operating point.
    stable = [r for r in rows if r.get("stable") in (True, "True", 1.0)]
    if not stable:
        print("[plot_queuing] no stable rows to plot vs R", file=sys.stderr)
        return
    n0 = sorted({r["N"] for r in stable})[len(set(r["N"] for r in stable)) // 2]
    m0 = sorted({r["M"] for r in stable})[len(set(r["M"] for r in stable)) // 2]
    sel = [r for r in stable if r["N"] == n0 and r["M"] == m0]

    for metric in ("L", "Lq", "W", "Wq"):
        by_model = defaultdict(list)
        for r in sel:
            key = f"{r['model']} s={int(r['servers'])}"
            by_model[key].append((r["R"], r[metric]))
        fig = ax = None
        for key in sorted(by_model):
            pts = sorted(by_model[key])
            fig, ax = line_with_errorbars(
                [p[0] for p in pts], [p[1] for p in pts],
                label=key, ax=ax,
                xlabel="Server rate R", ylabel=metric,
                title=f"{metric} vs R  (N={n0:.0f}, M={m0:.0f})",
            )
        if fig is not None:
            save(fig, out / f"{metric}_vs_R.png")


def plot_vs_load(rows: list[dict], out) -> None:
    """Mean number in system L vs offered load lambda = N/M, per server count."""
    stable = [r for r in rows if r.get("stable") in (True, "True", 1.0)]
    if not stable:
        return
    r0 = sorted({r["R"] for r in stable})[len(set(r["R"] for r in stable)) // 2]
    sel = [r for r in stable if r["R"] == r0]
    by_s = defaultdict(list)
    for r in sel:
        by_s[int(r["servers"])].append((r["lambda"], r["L"]))
    fig = ax = None
    for s in sorted(by_s):
        pts = sorted(by_s[s])
        fig, ax = line_with_errorbars(
            [p[0] for p in pts], [p[1] for p in pts],
            label=f"s={s}", ax=ax,
            xlabel="Arrival rate lambda = N/M", ylabel="L (jobs in system)",
            title=f"L vs arrival load  (R={r0:.0f})",
        )
    if fig is not None:
        save(fig, out / "L_vs_load.png")


def plot_randomness(rows: list[dict], out) -> None:
    """Bar comparison of W / Wq across the three distributions."""
    by_dist = defaultdict(lambda: defaultdict(list))
    for r in rows:
        by_dist[r["service_dist"]]["W"].append(r["W"])
        by_dist[r["service_dist"]]["Wq"].append(r["Wq"])
    dists = sorted(by_dist)
    if not dists:
        return
    series = {
        "W (time in system)": [
            sum(by_dist[d]["W"]) / len(by_dist[d]["W"]) for d in dists
        ],
        "Wq (queue wait)": [
            sum(by_dist[d]["Wq"]) / len(by_dist[d]["Wq"]) for d in dists
        ],
    }
    fig, _ = bar_compare(
        dists, series,
        xlabel="Distribution", ylabel="Mean time",
        title="Randomness study: queueing delay by distribution",
    )
    save(fig, out / "randomness_W_Wq.png")


def main(argv: list[str] | None = None) -> int:
    out = FIGURES_DIR / "queuing"
    analytic = RESULTS_DIR / "mq_analytic.csv"
    if not analytic.exists():
        print(f"[plot_queuing] missing {analytic}; run run_queuing.py first",
              file=sys.stderr)
        return 1

    rows = load_rows(analytic)
    print(f"[plot_queuing] {len(rows)} analytic rows -> {out}/", file=sys.stderr)
    plot_vs_R(rows, out)
    plot_vs_load(rows, out)

    randomness = RESULTS_DIR / "mq_randomness.csv"
    if randomness.exists():
        plot_randomness(load_rows(randomness), out)
        print("[plot_queuing] randomness figure written.", file=sys.stderr)

    print("[plot_queuing] done.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
