# Paper 3 — Scheduling & Queuing

Part II §2 + §3 of the OS final project: optimisation of a three-level
Multilevel Feedback Queue (MLFQ) scheduler, plus an M/M/1 and M/M/S queueing
analysis. Owner: **@endri**.

## Layout

```
mlfq/        MLFQ simulation engine
  process.py     Process model + random workload generator
  simulator.py   3-level MLFQ scheduler (variants A and B)
  metrics.py     throughput / turnaround / waiting / response
queuing/     queueing-theory models
  distributions.py  exponential / uniform / poisson samplers
  models.py         closed-form M/M/1 and M/M/S formulas
  simulation.py     discrete-event s-server FCFS simulator
drivers/     experiment runners + plotters
  run_mlfq.py       Monte Carlo grid search over Q1,Q2,L1,L2[,T]
  run_queuing.py    M/M/1 / M/M/S sweeps + randomness study
  plot_mlfq.py      heatmaps + 2D + 3D surfaces
  plot_queuing.py   diagrams vs R, vs load; randomness comparison
results/     CSV output
figures/     PNG output (mlfq/, queuing/)
report/      paper3.docx + OUTLINE.md
```

All parameter grids and seeds come from `../config/experiments.yaml`
(`paper3:` block). The two `mlfq/` and `queuing/` directories are importable
packages; the drivers wire up `sys.path` via `drivers/_p3_common.py`.

## Quick start

```bash
bash paper3-scheduling/smoke.sh          # coarse end-to-end check (<1 min)
```

## Full runs

```bash
# MLFQ grid search -- full config grid, 300 Monte Carlo trials
python paper3-scheduling/drivers/run_mlfq.py --variant A --full --trials 300
python paper3-scheduling/drivers/run_mlfq.py --variant B --full --trials 300

# Queueing: analytic sweep + simulated randomness study
python paper3-scheduling/drivers/run_queuing.py --simulate

# Figures
python paper3-scheduling/drivers/plot_mlfq.py --variant A
python paper3-scheduling/drivers/plot_mlfq.py --variant B
python paper3-scheduling/drivers/plot_queuing.py
```

The full MLFQ grid (Q1×Q2×L1×L2[×T]) × 300 trials × N=1000 is large — as with
Paper 2's sweep, trim the grid in `config/experiments.yaml` if the real run is
too slow on the VM. The coarse default grid in `run_mlfq.py` is the smoke
subset.

## Modelling note

The level allotments L1/L2/L3 are read as a **scheduler duty cycle** (the CPU
spends L1, L2, L3 of every 100-unit super-cycle on levels 0, 1, 2), not as
per-process CPU allotments — a per-process reading is impossible because bursts
reach 1000 units while L1+L2+L3 = 100. The full reasoning is in the
`mlfq/simulator.py` module docstring; if the course expects a different
reading, only that file changes.
