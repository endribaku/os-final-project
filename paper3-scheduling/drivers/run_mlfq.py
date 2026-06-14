"""
drivers/run_mlfq.py
Monte Carlo grid search over the MLFQ scheduler parameters (Paper 3 §2, §6).

For every valid (Q1, Q2, L1, L2[, T]) combination the driver runs `trials`
independent simulations -- each with a freshly generated random workload -- and
writes one CSV row holding the trial-averaged metrics. After the sweep it
prints the optimal configuration for each of the four objectives.

Usage
-----
    # fast smoke run on a coarse grid
    python paper3-scheduling/drivers/run_mlfq.py --variant A

    # full grid from config/experiments.yaml (long -- reduce first if needed)
    python paper3-scheduling/drivers/run_mlfq.py --variant A --full --trials 300

Output: paper3-scheduling/results/mlfq_<variant>.csv

Note on cost: the full config grid (Q1 x Q2 x L1 x L2 [x T]) times 300 trials
times N=1000 processes is large -- exactly as Paper 2's sweep was reduced to
fit the ARM VM, the MLFQ grid should be trimmed for the real run. The coarse
default grid below is the smoke-test subset.
"""
from __future__ import annotations

import argparse
import itertools
import multiprocessing as mp
import os
import random
import sys
import time
from functools import partial

from _p3_common import RESULTS_DIR, CsvSink, global_seeds, paper3_cfg

from mlfq import MLFQConfig, generate_processes, simulate, summarize
from mlfq.metrics import mean_of

# Coarse default grid -- a smoke-test subset of the full config grid.
COARSE = {
    "Q1": [2, 8, 20],
    "Q2": [8, 24, 48],
    "L1": [20, 40],
    "L2": [30, 50],
    "T":  [0, 50, 100],
}

OBJECTIVES = [
    ("throughput", "max"),
    ("turnaround_mean", "min"),
    ("waiting_mean", "min"),
    ("response_mean", "min"),
]


def build_grid(cfg: dict, variant: str, full: bool) -> list[MLFQConfig]:
    """Materialise every valid MLFQConfig for the requested grid."""
    mlfq = cfg["mlfq"]
    cycle = mlfq["total_level_time_ms"]
    if full:
        q1s, q2s = mlfq["Q1_grid"], mlfq["Q2_grid"]
        l1s, l2s = mlfq["L1_grid"], mlfq["L2_grid"]
        ts = mlfq["T_grid"]
    else:
        q1s, q2s = COARSE["Q1"], COARSE["Q2"]
        l1s, l2s = COARSE["L1"], COARSE["L2"]
        ts = COARSE["T"]

    t_values = ts if variant == "B" else [0]
    grid: list[MLFQConfig] = []
    for q1, q2, l1, l2, t in itertools.product(q1s, q2s, l1s, l2s, t_values):
        c = MLFQConfig(q1=q1, q2=q2, l1=l1, l2=l2, cycle=cycle,
                       variant=variant, t_split=t)
        if c.is_valid():
            grid.append(c)
    return grid


def evaluate(config: MLFQConfig, n: int, m: float, trials: int,
             seeds: list[int], arrival_dist: str, burst_range: tuple[int, int]
             ) -> dict:
    """Run `trials` simulations of `config`; return trial-averaged metrics.

    The per-trial seed is a deterministic function of the trial index, so the
    averaged result is identical whether configs run serially or in parallel.
    """
    runs = []
    for t in range(trials):
        seed = seeds[t % len(seeds)] * 100_003 + t  # spread seeds across trials
        rng = random.Random(seed)
        procs = generate_processes(n, m, burst_range=burst_range,
                                   arrival_dist=arrival_dist, rng=rng)
        sim = simulate(procs, config)
        runs.append(summarize(sim.procs, sim.context_switches))
    return {k: mean_of(runs, k) for k in runs[0]}


def _worker(config: MLFQConfig, params: dict) -> tuple[MLFQConfig, dict]:
    """multiprocessing.Pool worker -- evaluate one config (module-level so it
    is picklable). Each config is independent, so the grid parallelises
    cleanly across cores."""
    return config, evaluate(
        config, params["n"], params["m"], params["trials"],
        params["seeds"], params["arrival_dist"], params["burst_range"],
    )


def main(argv: list[str] | None = None) -> int:
    cfg = paper3_cfg()
    mlfq = cfg["mlfq"]

    ap = argparse.ArgumentParser(description="MLFQ Monte Carlo grid search.")
    ap.add_argument("--variant", choices=["A", "B"], default="A")
    ap.add_argument("--full", action="store_true",
                    help="use the full config grid instead of the coarse one")
    ap.add_argument("--trials", type=int, default=10,
                    help="Monte Carlo trials per config (config: 300)")
    ap.add_argument("--n", type=int, default=200, help="processes per trial")
    ap.add_argument("--m", type=float, default=100.0, help="arrival window width")
    ap.add_argument("--arrival-dist", default="uniform",
                    choices=["uniform", "exponential", "poisson"])
    ap.add_argument("--out", default=None, help="output CSV path override")
    ap.add_argument("--jobs", type=int, default=0,
                    help="parallel worker processes (0 = all CPU cores)")
    args = ap.parse_args(argv)

    burst_range = tuple(mlfq["burst_range"])
    seeds = global_seeds()
    grid = build_grid(cfg, args.variant, args.full)
    out_path = (RESULTS_DIR / f"mlfq_{args.variant}.csv"
                if args.out is None else args.out)
    jobs = args.jobs if args.jobs > 0 else (os.cpu_count() or 1)

    print(f"[run_mlfq] variant={args.variant} configs={len(grid)} "
          f"trials={args.trials} N={args.n} M={args.m} jobs={jobs} -> {out_path}",
          file=sys.stderr)

    params = {
        "n": args.n, "m": args.m, "trials": args.trials, "seeds": seeds,
        "arrival_dist": args.arrival_dist, "burst_range": burst_range,
    }
    best: dict[str, tuple[float, dict]] = {}
    started = time.time()

    # The grid parallelises across cores -- one process per config. imap_un-
    # ordered streams results back as workers finish so the CSV and progress
    # line update live; trial seeding is index-based so results are identical
    # to a serial run.
    with CsvSink(out_path) as sink, mp.Pool(jobs) as pool:
        stream = pool.imap_unordered(partial(_worker, params=params), grid)
        for i, (config, metrics) in enumerate(stream, 1):
            row = {
                "variant": config.variant,
                "Q1": config.q1, "Q2": config.q2,
                "L1": config.l1, "L2": config.l2, "L3": config.l3,
                "T": config.t_split,
                "N": args.n, "M": args.m,
                "trials": args.trials,
                "arrival_dist": args.arrival_dist,
                **metrics,
            }
            sink.write(row)
            for key, direction in OBJECTIVES:
                val = row[key]
                if key not in best or (
                    (direction == "max" and val > best[key][0])
                    or (direction == "min" and val < best[key][0])
                ):
                    best[key] = (val, row)
            if i % 10 == 0 or i == len(grid):
                print(f"  [{i}/{len(grid)}] {time.time()-started:.1f}s",
                      file=sys.stderr)

    print(f"\n[run_mlfq] done in {time.time()-started:.1f}s. Optimal configs:")
    for key, direction in OBJECTIVES:
        val, row = best[key]
        print(f"  {direction} {key:16s} = {val:12.4f}  at "
              f"Q1={row['Q1']} Q2={row['Q2']} L1={row['L1']} L2={row['L2']}"
              + (f" T={row['T']}" if args.variant == "B" else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
