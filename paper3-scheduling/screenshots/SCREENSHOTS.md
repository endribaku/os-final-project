# Paper 3 — Simulation screenshots playbook

The PDF asks for "all simulation screenshots". Paper 3's simulations are pure
Python and machine-independent, so the screenshots can be taken on either the
VM or your Mac and look identical. Four shots cover the full pipeline.

## Procedure

1. `cd ~/os-final-project` on whichever machine you're using.
2. For each shot below: run the command in a Terminal, press **`PrtSc`** (VM)
   or **`Cmd+Shift+4`** then drag (macOS) to capture the Terminal window, save
   the PNG to `paper3-scheduling/screenshots/` with the suggested filename.

If you're on the VM, use `python3`. On your Mac use `.venv/bin/python`.

## Shots

### 01 — MLFQ variant A optimisation output
```bash
.venv/bin/python paper3-scheduling/drivers/run_mlfq.py \
    --variant A --trials 5 --n 100
```
Capture as: `01-mlfq-A-optimal.png` — shows the per-config progress lines and
the four "Optimal configs" lines at the end (the headline result of §6).

### 02 — MLFQ variant B optimisation output
```bash
.venv/bin/python paper3-scheduling/drivers/run_mlfq.py \
    --variant B --trials 5 --n 100
```
Capture as: `02-mlfq-B-optimal.png` — same kind of output, but with the
`T` parameter included in each optimal config (proves the SJF/FCFS split).

### 03 — Queueing analytic + randomness study finishing
```bash
.venv/bin/python paper3-scheduling/drivers/run_queuing.py \
    --simulate --arrivals 10000
```
Capture as: `03-queuing-simulate.png` — shows both "analytic: 135 rows" and
"randomness study: 132 rows" lines.

### 04 — Real-run sweep log (already captured)
```bash
less paper3-scheduling/results/sweep_log.txt
```
Or `cat` it and scroll; capture the screen showing the variant-A "Optimal
configs" block and the variant-B start line.
Capture as: `04-sweep-log.png` — this is the actual log from the real
sweep, not a demo run.

## After capturing

Drop the four PNGs in this folder. When paper3.md is drafted, its Appendix
"Simulation screenshots" will embed them. Regenerate with the same pandoc
command pattern that paper 2 uses (see `paper2-concurrency/report/`).
