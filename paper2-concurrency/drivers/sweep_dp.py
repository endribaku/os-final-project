#!/usr/bin/env python3
"""
Sweep driver for the Dining Philosophers experiments (Paper 2 §B).

Reads `paper2.dining_philosophers` from config/experiments.yaml and runs each
(impl, P-philosophers, seed) combo under common.bench.run. Each binary's JSON
line on stdout is merged with the bench system metrics into one CSV row.

Output: paper2-concurrency/results/dp_sweep.csv (appends).

Run examples:
    # full sweep (all impls × all P × all seeds × global.repetitions per seed)
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_dp.py

    # smoke
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_dp.py --quick

    # only the naive C variant -- useful for deadlock-frequency runs
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_dp.py \\
        --impls c-pthreads-naive --duration-sec 30 --deadlock-window-ms 2000
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sweep_common import (  # noqa: E402
    ROOT, CsvSink, load_cfg, make_row, parse_json_line, run_one,
)

IMPLS = {
    "java-monitor":         "java -cp {jdir} DiningMonitor",
    "java-semaphore":       "java -cp {jdir} DiningSemaphore",
    "java-hierarchy":       "java -cp {jdir} DiningHierarchy",
    "c-pthreads-monitor":   "{cdir}/dphil_5",
    "c-pthreads-hierarchy": "{cdir}/dphil_4",
    "c-pthreads-naive":     "{cdir}/dphil_2",
}


def build_cmd(impl: str, *, P, duration_sec, tmin, tmax, emin, emax,
              seed, deadlock_window_ms) -> str:
    jdir = ROOT / "paper2-concurrency" / "dp" / "java"
    cdir = ROOT / "paper2-concurrency" / "dp" / "pthreads"
    prefix = IMPLS[impl].format(jdir=jdir, cdir=cdir)
    return (f"{prefix} --N {P} --duration-sec {duration_sec} "
            f"--think-min-ms {tmin} --think-max-ms {tmax} "
            f"--eat-min-ms {emin} --eat-max-ms {emax} "
            f"--seed {seed} --deadlock-window-ms {deadlock_window_ms}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impls", nargs="*", choices=list(IMPLS), default=list(IMPLS))
    ap.add_argument("--Ps", type=int, nargs="*", default=None,
                    help="Override P values from config.")
    ap.add_argument("--seeds", type=int, nargs="*", default=None,
                    help="Override seeds from config.")
    ap.add_argument("--reps", type=int, default=None,
                    help="Reps per (impl, P, seed). Default: global.repetitions.")
    ap.add_argument("--duration-sec", type=float, default=None,
                    help="Override run duration.")
    ap.add_argument("--deadlock-window-ms", type=int, default=None,
                    help="Override watchdog window.")
    ap.add_argument("--quick", action="store_true",
                    help="Smoke-size grid: P=5, 1 seed, 1 rep, 1s duration.")
    ap.add_argument("--out", type=str,
                    default=str(ROOT / "paper2-concurrency/results/dp_sweep.csv"))
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = load_cfg()
    dpc = cfg["paper2"]["dining_philosophers"]
    g = cfg["global"]

    Ps        = args.Ps or dpc["P_philosophers"]
    seeds     = args.seeds or g["seeds"]
    reps      = args.reps if args.reps is not None else g["repetitions"]
    duration  = args.duration_sec if args.duration_sec is not None else dpc["run_seconds"]
    tmin, tmax = dpc["think_delay_ms"]
    emin, emax = dpc["eat_delay_ms"]
    dlw       = args.deadlock_window_ms if args.deadlock_window_ms is not None \
                else dpc["deadlock_detect_ms"]

    if args.quick:
        Ps = Ps[:1]
        seeds = seeds[:1]
        reps = 1
        duration = min(duration, 1.0)

    combos = list(itertools.product(args.impls, Ps, seeds))
    print(f"[sweep_dp] {len(combos)} (impl,P,seed) tuples × {reps} reps "
          f"= {len(combos) * reps} runs, each ~{duration}s",
          file=sys.stderr)

    sink = CsvSink(Path(args.out))
    try:
        for combo_idx, (impl, P, seed) in enumerate(combos, start=1):
            cmd = build_cmd(impl, P=P, duration_sec=duration,
                            tmin=tmin, tmax=tmax, emin=emin, emax=emax,
                            seed=seed, deadlock_window_ms=dlw)
            label = f"{combo_idx}/{len(combos)} {impl} P={P} seed={seed}"
            results = run_one(cmd, reps, label=label, dry=args.dry_run)
            for rep_idx, br in enumerate(results):
                app = parse_json_line(br.stdout)
                if not app:
                    print(f"[sweep_dp] WARN: bad JSON on rep {rep_idx} of {cmd!r}",
                          file=sys.stderr)
                    continue
                sink.write(make_row(br, app, seed=seed, rep_idx=rep_idx))
    finally:
        sink.close()
    print(f"[sweep_dp] wrote -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
