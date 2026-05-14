#!/usr/bin/env python3
"""
Stress-test runner for Paper 2.

Defines a fixed set of stress configurations that probe edge-cases the
"normal" sweeps don't reach. Each test pushes the synchronisation primitives
toward a failure mode (max contention, asymmetric load, large N, starvation,
or outright deadlock).

Tests:
    pc-tiny         N=1 buffer, M=K=8, no delay         -- max-contention PC
    pc-asym-prod    N=4, M=16, K=1, no delay            -- producers >> consumers
    pc-asym-cons    N=4, M=1, K=16, no delay            -- consumers >> producers
    pc-long         N=64, M=K=4, 1e6 items/producer     -- steady-state stability
    dp-deadlock     naive C only, P=5/10/20 × 10 seeds  -- provoke deadlock
    dp-large-N      safe impls, P=50/100/200            -- scalability stress
    dp-starvation   all impls, eat>>think, P=10         -- fairness stress

Outputs: paper2-concurrency/results/stress/<test_name>.csv (one CSV per test).

Usage:
    PYTHONPATH=. python paper2-concurrency/drivers/stress.py              # all
    PYTHONPATH=. python paper2-concurrency/drivers/stress.py --quick      # smoke
    PYTHONPATH=. python paper2-concurrency/drivers/stress.py --test dp-deadlock
    PYTHONPATH=. python paper2-concurrency/drivers/stress.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sweep_common import (  # noqa: E402
    ROOT, CsvSink, make_row, parse_json_line, run_one,
)

PC_JAVA = ROOT / "paper2-concurrency/pc/java"
PC_C    = ROOT / "paper2-concurrency/pc/pthreads"
DP_JAVA = ROOT / "paper2-concurrency/dp/java"
DP_C    = ROOT / "paper2-concurrency/dp/pthreads"

DEFAULT_OUT_DIR = ROOT / "paper2-concurrency/results/stress"

DP_JAVA_CLASS = {
    "monitor":   "DiningMonitor",
    "semaphore": "DiningSemaphore",
    "hierarchy": "DiningHierarchy",
}
DP_C_BIN = {
    "naive":     "dphil_2",
    "hierarchy": "dphil_4",
    "monitor":   "dphil_5",
}


# ---- command builders ---------------------------------------------------

def pc_java_cmd(*, N, M, K, items, pdel=0, cdel=0) -> str:
    return (f"java -cp {PC_JAVA} ProducerConsumer "
            f"--N {N} --M {M} --K {K} --items {items} "
            f"--producer-delay-us {pdel} --consumer-delay-us {cdel}")


def pc_c_cmd(*, N, M, K, items, pdel=0, cdel=0) -> str:
    return (f"{PC_C}/producer_consumer "
            f"--N {N} --M {M} --K {K} --items {items} "
            f"--producer-delay-us {pdel} --consumer-delay-us {cdel}")


def dp_java_cmd(impl, *, P, dur, tmin, tmax, emin, emax, seed, dlw=5000) -> str:
    return (f"java -cp {DP_JAVA} {DP_JAVA_CLASS[impl]} "
            f"--N {P} --duration-sec {dur} "
            f"--think-min-ms {tmin} --think-max-ms {tmax} "
            f"--eat-min-ms {emin} --eat-max-ms {emax} "
            f"--seed {seed} --deadlock-window-ms {dlw}")


def dp_c_cmd(impl, *, P, dur, tmin, tmax, emin, emax, seed, dlw=5000) -> str:
    return (f"{DP_C}/{DP_C_BIN[impl]} "
            f"--N {P} --duration-sec {dur} "
            f"--think-min-ms {tmin} --think-max-ms {tmax} "
            f"--eat-min-ms {emin} --eat-max-ms {emax} "
            f"--seed {seed} --deadlock-window-ms {dlw}")


# ---- config table -------------------------------------------------------
# Each entry is (test_name, cmd, reps). Each test_name groups runs into one CSV.

def build_stress_configs() -> list[tuple[str, str, int]]:
    cfgs: list[tuple[str, str, int]] = []

    # 1. PC tiny buffer, max contention
    for builder in (pc_java_cmd, pc_c_cmd):
        cfgs.append(("pc-tiny", builder(N=1, M=8, K=8, items=50_000), 5))

    # 2. asymmetric producers >> consumers
    for builder in (pc_java_cmd, pc_c_cmd):
        cfgs.append(("pc-asym-prod", builder(N=4, M=16, K=1, items=20_000), 5))

    # 3. asymmetric consumers >> producers
    for builder in (pc_java_cmd, pc_c_cmd):
        cfgs.append(("pc-asym-cons", builder(N=4, M=1, K=16, items=20_000), 5))

    # 4. PC long steady-state (heavy total volume)
    for builder in (pc_java_cmd, pc_c_cmd):
        cfgs.append(("pc-long", builder(N=64, M=4, K=4, items=1_000_000), 3))

    # 5. DP deadlock provocation: naive C, P=5/10/20, 10 seeds each.
    #    think=0 + long eat + tight watchdog window => high deadlock rate.
    for P in (5, 10, 20):
        for seed in range(1, 11):
            cfgs.append(("dp-deadlock",
                         dp_c_cmd("naive", P=P, dur=10,
                                  tmin=0, tmax=0, emin=50, emax=200,
                                  seed=seed, dlw=2000),
                         1))

    # 6. DP large-N scalability. Safe impls only (no deadlocks expected).
    LARGE_N = (50, 100, 200)
    for impl in ("monitor", "semaphore", "hierarchy"):
        for P in LARGE_N:
            cfgs.append(("dp-large-N",
                         dp_java_cmd(impl, P=P, dur=10,
                                     tmin=10, tmax=50, emin=10, emax=50, seed=42),
                         3))
    for impl in ("monitor", "hierarchy"):
        for P in LARGE_N:
            cfgs.append(("dp-large-N",
                         dp_c_cmd(impl, P=P, dur=10,
                                  tmin=10, tmax=50, emin=10, emax=50, seed=42),
                         3))

    # 7. DP starvation: eat-heavy load, see how fair each impl is.
    for impl in ("monitor", "semaphore", "hierarchy"):
        cfgs.append(("dp-starvation",
                     dp_java_cmd(impl, P=10, dur=15,
                                 tmin=5, tmax=10, emin=100, emax=500, seed=42),
                     3))
    for impl in ("monitor", "hierarchy"):
        cfgs.append(("dp-starvation",
                     dp_c_cmd(impl, P=10, dur=15,
                              tmin=5, tmax=10, emin=100, emax=500, seed=42),
                     3))

    return cfgs


def _filter_quick(cfgs: list[tuple[str, str, int]]) -> list[tuple[str, str, int]]:
    """Keep just the first config of each test name, reps=1."""
    seen: set[str] = set()
    out: list[tuple[str, str, int]] = []
    for name, cmd, _reps in cfgs:
        if name in seen:
            continue
        seen.add(name)
        out.append((name, cmd, 1))
    return out


# ---- main ---------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--test", default="all",
                    help="Run only this test "
                         "(pc-tiny / pc-asym-prod / pc-asym-cons / pc-long / "
                         "dp-deadlock / dp-large-N / dp-starvation / all).")
    ap.add_argument("--quick", action="store_true",
                    help="Only one run per test, for smoke-testing.")
    ap.add_argument("--out-dir", type=str, default=str(DEFAULT_OUT_DIR))
    ap.add_argument("--dry-run", action="store_true",
                    help="Print commands without executing.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    cfgs = build_stress_configs()
    if args.test != "all":
        cfgs = [c for c in cfgs if c[0] == args.test]
        if not cfgs:
            valid = sorted({c[0] for c in build_stress_configs()})
            print(f"No stress configs match --test={args.test}\n"
                  f"valid: {', '.join(valid)}", file=sys.stderr)
            return 2
    if args.quick:
        cfgs = _filter_quick(cfgs)

    total_runs = sum(r for _, _, r in cfgs)
    print(f"[stress] {len(cfgs)} configs, {total_runs} total runs "
          f"-> {out_dir}", file=sys.stderr)

    sinks: dict[str, CsvSink] = {}
    try:
        for i, (test_name, cmd, reps) in enumerate(cfgs, start=1):
            label = f"{i}/{len(cfgs)} {test_name}"
            results = run_one(cmd, reps, label=label, dry=args.dry_run)
            sink = sinks.setdefault(
                test_name, CsvSink(out_dir / f"{test_name}.csv"))
            for rep_idx, br in enumerate(results):
                app = parse_json_line(br.stdout)
                if not app:
                    print(f"[stress] WARN bad JSON in {test_name}: {cmd!r}",
                          file=sys.stderr)
                    continue
                sink.write(make_row(br, app, test=test_name, rep_idx=rep_idx))
    finally:
        for s in sinks.values():
            s.close()

    print(f"[stress] CSVs -> {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
