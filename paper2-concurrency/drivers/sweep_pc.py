#!/usr/bin/env python3
"""
Sweep driver for the Producer-Consumer experiments (Paper 2 §A).

Reads `paper2.producer_consumer` from config/experiments.yaml and runs every
(impl, N, M, K, producer_delay, consumer_delay) combo under common.bench.run.
Each run's JSON line on stdout is merged with the bench system metrics into
one CSV row.

Output: paper2-concurrency/results/pc_sweep.csv (appends).

Run examples:
    # full sweep
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_pc.py

    # smoke (single value per axis)
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_pc.py --quick

    # only the Java impl
    PYTHONPATH=. python paper2-concurrency/drivers/sweep_pc.py --impls java-monitor
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

# fix import when run as a script (PYTHONPATH=. takes care of `common`)
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _sweep_common import (  # noqa: E402
    ROOT, CsvSink, load_cfg, make_row, parse_json_line, run_one,
)

IMPLS = {
    "java-monitor":   "java -cp {jdir} ProducerConsumer",
    "java-lockfree":  "java -cp {jdir} ProducerConsumerLockFree",
    "c-pthreads-sem": "{cdir}/producer_consumer",
}


def build_cmd(impl: str, *, N, M, K, items, pdelay, cdelay) -> str:
    jdir = ROOT / "paper2-concurrency" / "pc" / "java"
    cdir = ROOT / "paper2-concurrency" / "pc" / "pthreads"
    prefix = IMPLS[impl].format(jdir=jdir, cdir=cdir)
    return (f"{prefix} --N {N} --M {M} --K {K} --items {items} "
            f"--producer-delay-us {pdelay} --consumer-delay-us {cdelay}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--impls", nargs="*", choices=list(IMPLS), default=list(IMPLS))
    ap.add_argument("--reps", type=int, default=None,
                    help="Repetitions per config (default: global.repetitions).")
    ap.add_argument("--quick", action="store_true",
                    help="Smoke-size grid: 1 value per axis, 2 reps.")
    ap.add_argument("--out", type=str,
                    default=str(ROOT / "paper2-concurrency/results/pc_sweep.csv"))
    ap.add_argument("--dry-run", action="store_true",
                    help="Print commands; don't execute.")
    args = ap.parse_args()

    cfg = load_cfg()
    pc = cfg["paper2"]["producer_consumer"]
    reps = args.reps if args.reps is not None else cfg["global"]["repetitions"]

    if args.quick:
        Ns = pc["N_buffer"][-1:]                  # one buffer size
        Ms = [pc["M_producers"][1] if len(pc["M_producers"]) > 1 else pc["M_producers"][0]]
        Ks = [pc["K_consumers"][1] if len(pc["K_consumers"]) > 1 else pc["K_consumers"][0]]
        pdelays = pc["producer_delay_us"][:1]
        cdelays = pc["consumer_delay_us"][:1]
        reps = min(reps, 2)
        items = max(1000, pc["items_per_producer"] // 10)
    else:
        Ns       = pc["N_buffer"]
        Ms       = pc["M_producers"]
        Ks       = pc["K_consumers"]
        pdelays  = pc["producer_delay_us"]
        cdelays  = pc["consumer_delay_us"]
        items    = pc["items_per_producer"]

    combos = list(itertools.product(args.impls, Ns, Ms, Ks, pdelays, cdelays))
    print(f"[sweep_pc] {len(combos)} configs × {reps} reps "
          f"= {len(combos) * reps} runs", file=sys.stderr)

    sink = CsvSink(Path(args.out))
    try:
        for combo_idx, (impl, N, M, K, pdel, cdel) in enumerate(combos, start=1):
            cmd = build_cmd(impl, N=N, M=M, K=K, items=items,
                            pdelay=pdel, cdelay=cdel)
            label = f"{combo_idx}/{len(combos)} {impl}"
            results = run_one(cmd, reps, label=label, dry=args.dry_run)
            for rep_idx, br in enumerate(results):
                app = parse_json_line(br.stdout)
                if not app:
                    print(f"[sweep_pc] WARN: bad JSON on rep {rep_idx} of {cmd!r}",
                          file=sys.stderr)
                    continue
                sink.write(make_row(br, app, rep_idx=rep_idx))
    finally:
        sink.close()
    print(f"[sweep_pc] wrote -> {args.out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
