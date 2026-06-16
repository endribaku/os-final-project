"""
drivers/run_queuing.py
M/M/1 and M/M/S queueing sweeps (Paper 3 §3).

Two things, both written to paper3-scheduling/results/:

  1. mq_analytic.csv -- closed-form M/M/1 and M/M/S quantities swept over the
     constant (N, M, R) grid and the server-count grid. The project's "N, M, R
     constant over time" case: lambda = N/M, mu = R.

  2. mq_randomness.csv (with --simulate) -- the randomness study: the same
     operating points fed to the discrete-event simulator under each of the
     three distributions (exponential / uniform / poisson). The exponential row
     should match the analytic value; the others quantify the shape effect.

Usage
-----
    python paper3-scheduling/drivers/run_queuing.py
    python paper3-scheduling/drivers/run_queuing.py --simulate --arrivals 50000
"""
from __future__ import annotations

import argparse
import random
import sys
import time

from _p3_common import RESULTS_DIR, CsvSink, global_seeds, paper3_cfg

from queuing import mm1_metrics, mms_metrics, simulate_queue


def analytic_sweep(cfg: dict, sink: CsvSink) -> int:
    """Closed-form M/M/1 + M/M/S over the constant (N, M, R) grid."""
    q = cfg["queuing"]
    grid = q["constant_grid"]
    rows = 0
    for n in grid["N"]:
        for m in grid["M"]:
            for r in grid["R"]:
                lam = n / m            # arrival rate
                mu = float(r)          # per-server service rate
                # M/M/1
                row = mm1_metrics(lam, mu).as_row()
                row.update(N=n, M=m, R=r)
                sink.write(row)
                rows += 1
                # M/M/S for every server count in the grid
                for s in q["S_servers"]:
                    row = mms_metrics(lam, mu, s).as_row()
                    row.update(N=n, M=m, R=r)
                    sink.write(row)
                    rows += 1
    return rows


def randomness_sweep(cfg: dict, sink: CsvSink, n_arrivals: int,
                     warmup: int, seeds: list[int]) -> int:
    """Simulate each operating point under all three distributions."""
    q = cfg["queuing"]
    grid = q["constant_grid"]
    dists = q["distributions"]
    rows = 0
    for n in grid["N"]:
        for m in grid["M"]:
            for r in grid["R"]:
                lam = n / m
                mu = float(r)
                if lam / mu >= 1.0:
                    continue  # unstable -- simulator would not converge
                for s in [1] + [x for x in q["S_servers"] if x > 1]:
                    if lam / (s * mu) >= 1.0:
                        continue
                    for dist in dists:
                        res = simulate_queue(
                            lam, mu, servers=s,
                            n_arrivals=n_arrivals, warmup=warmup,
                            arrival_dist=dist, service_dist=dist,
                            rng=random.Random(seeds[0] * 911 + s),
                        )
                        row = res.as_row()
                        row.update(N=n, M=m, R=r)
                        sink.write(row)
                        rows += 1
    return rows


def main(argv: list[str] | None = None) -> int:
    cfg = paper3_cfg()
    q = cfg["queuing"]

    ap = argparse.ArgumentParser(description="M/M/1 and M/M/S queueing sweeps.")
    ap.add_argument("--simulate", action="store_true",
                    help="also run the discrete-event randomness study")
    ap.add_argument("--arrivals", type=int, default=q["steady_state_arrivals"],
                    help="customers per simulation (config default)")
    ap.add_argument("--warmup", type=int, default=q["warmup_arrivals"])
    args = ap.parse_args(argv)

    seeds = global_seeds()
    started = time.time()

    with CsvSink(RESULTS_DIR / "mq_analytic.csv") as sink:
        n = analytic_sweep(cfg, sink)
    print(f"[run_queuing] analytic: {n} rows -> results/mq_analytic.csv "
          f"({time.time()-started:.1f}s)", file=sys.stderr)

    if args.simulate:
        with CsvSink(RESULTS_DIR / "mq_randomness.csv") as sink:
            n = randomness_sweep(cfg, sink, args.arrivals, args.warmup, seeds)
        print(f"[run_queuing] randomness study: {n} rows -> "
              f"results/mq_randomness.csv ({time.time()-started:.1f}s)",
              file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
