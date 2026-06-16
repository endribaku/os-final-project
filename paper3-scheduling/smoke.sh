#!/usr/bin/env bash
# paper3-scheduling/smoke.sh
# Fast end-to-end check: runs the coarse MLFQ grid (both variants), the
# analytic queueing sweep, and all plotters. Should finish in well under a
# minute. The real Monte Carlo runs use run_mlfq.py --full --trials 300 and
# run_queuing.py --simulate; see README.md.
set -euo pipefail
cd "$(dirname "$0")"
DRV=drivers

echo "== MLFQ variant A (coarse grid) =="
python "$DRV/run_mlfq.py" --variant A --trials 5 --n 120

echo "== MLFQ variant B (coarse grid) =="
python "$DRV/run_mlfq.py" --variant B --trials 5 --n 120

echo "== Queueing analytic sweep =="
python "$DRV/run_queuing.py"

echo "== Queueing randomness study (short) =="
python "$DRV/run_queuing.py" --simulate --arrivals 8000 --warmup 1000

echo "== Plots =="
python "$DRV/plot_mlfq.py" --variant A
python "$DRV/plot_mlfq.py" --variant B
python "$DRV/plot_queuing.py"

echo "== smoke OK =="
ls -la results/ figures/mlfq/ figures/queuing/
