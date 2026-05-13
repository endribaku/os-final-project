# Tasks

Split: **@endri** owns Part II (Papers 2 + 3). **@hazis** owns Part I (Paper 1).
Papers are independent — these tracks can run fully in parallel.

Tags: `@endri`, `@hazis`, `@both`.

---

## 0. Shared bootstrap (do first, together)

- [x] @both  Scaffold repo structure (`paper1-shell/`, `paper2-concurrency/`,
      `paper3-scheduling/`, `common/`, `config/`).
- [x] @both  Write `common/bench.py` (GNU-time wrapper → CSV).
- [x] @both  Write `common/plots.py` (matplotlib helpers: line+errorbars,
      heatmap, surface3d, bar_compare).
- [x] @both  Pin parameter ranges + seeds in `config/experiments.yaml`.
- [ ] @both  Finalize `ENVIRONMENT.md` (paste version output for both machines).
- [ ] @both  Decide Word vs Overleaf vs Google Doc for the master report; create
      the paper template (10 pt, 1-col, single-spaced, with Abstract / Keywords /
      Methodology / Results / Reproducibility / Appendix skeletons).
- [ ] @both  Create GitHub repo (private), push the scaffold, both clone.

---

## 1. Paper 1 — Shell Scripts (Part I)  *(owner: @hazis)*

### Code / experiments
- [ ] @hazis  Finalize the 10 scripts (current pre-fill: mailformat, rn,
      blank-rename, encryptedpw, collatz, days-between, game_of_life, primes,
      makedict, tree — swap if desired).
- [ ] @hazis  Add `echo`/logging to each of the 10 to expose intermediate
      results (commit to `paper1-shell/scripts/instrumented/`).
- [ ] @hazis  Run each script with varied inputs; capture screenshots + raw
      output into `paper1-shell/results/`.
- [ ] @hazis  Benchmark all 10 via `common/bench.py` → CSVs per script.
- [ ] @hazis  Write an optimized version of each of the 10
      (`paper1-shell/scripts/optimized/`).
- [ ] @hazis  Original-vs-optimized comparison runs + CSVs + plots.
- [ ] @hazis  CRT refactor of the section-2(a) modular-arithmetic script
      (`paper1-shell/crt/`); benchmark vs original.
- [ ] @hazis  Design + implement the **new tool**
      (`paper1-shell/newtool/`); evaluate it; algorithm description.
- [ ] @hazis  Design-patterns classification (pipeline / filter-transform /
      iterative / state-based) — pick examples from the 10.
- [ ] @hazis  Generate all final plots into `paper1-shell/figures/`.

### Writing  (5,000–8,000 words, 10–15 pp)
- [ ] @hazis  Intro · Experimental setup · per-script analysis
      (7 points × 10) · comparative optimization study · design patterns ·
      CRT case study · new tool · results & discussion · conclusion.
- [ ] @hazis  Abstract + Keywords + Reproducibility notes.
- [ ] @hazis  Appendix: full code, screenshots, raw runs.

---

## 2. Paper 2 — Concurrency (Part II §1)  *(owner: @endri)*

### Producer–Consumer (bounded buffer)
- [ ] @endri  Rename `paper2-concurrency/pc/python/` → `pc/java/`.
- [ ] @endri  Implement P–C in POSIX pthreads (`pc/pthreads/`).
- [ ] @endri  Implement P–C in Java (`pc/java/`).
- [ ] @endri  Parameterize: N (buffer), M (producers), K (consumers); read
      ranges from `config/experiments.yaml`.
- [ ] @endri  Sweep driver (Python) calling `common/bench.py`; dumps
      `paper2-concurrency/results/pc_<lang>.csv`.

### Dining Philosophers
- [ ] @endri  Rename `paper2-concurrency/dp/python/` → `dp/java/`.
- [ ] @endri  Implement DP in POSIX pthreads — testbed algorithms (monitor /
      semaphore / resource_hierarchy).
- [ ] @endri  Implement DP in Java — Baeldung-style + the lecture monitor
      solution (`monitor DiningPhilosophers { state[5]; ... }`).
- [ ] @endri  Parameterize to N philosophers; deadlock detection (no-progress
      window from config).
- [ ] @endri  Sweep driver; dumps `paper2-concurrency/results/dp_<lang>_<algo>.csv`.

### Analysis + plots
- [ ] @endri  Graphs vs N/M/K/P (time, CPU, memory, throughput, latency,
      context switches, deadlock frequency) into `paper2-concurrency/figures/`.
- [ ] @endri  Comparative analysis: POSIX vs Java, locks vs monitors vs
      semaphores, resource hierarchy effect.
- [ ] @endri  Stress tests.
- [ ] @endri  Optimization proposal (lock-free idea or adaptive buffer
      sizing) — write it; prototype + benchmark if time.

### Writing  (5,000–8,000 words, 10–15 pp)
- [ ] @endri  Intro · Related work · Methodology · Experimental design ·
      Performance evaluation · Scalability · Comparative analysis ·
      Optimization proposal · Discussion · Conclusion.
- [ ] @endri  Abstract + Keywords + Reproducibility notes.
- [ ] @endri  Appendix: full code, raw logs, all screenshots.

---

## 3. Paper 3 — Scheduling & Queuing (Part II §2 + §3)  *(owner: @endri)*

### MLFQ simulator
- [ ] @endri  Random process generator (N procs, burst [10–1000], arrivals
      [0–M]); reads grids from `config/experiments.yaml`.
- [ ] @endri  3-level MLFQ simulator (Q0 = RR Q1, Q1 = RR Q2, Q2 = FCFS;
      level allotments L1, L2, L3 = 100 − L1 − L2). Variant A.
- [ ] @endri  Variant B: level 3 = SJF for T% + FCFS for (100 − T)%.
- [ ] @endri  Monte Carlo runner (300 trials, sweep across N / M).
- [ ] @endri  Grid search over Q1, Q2, L1, L2 (and T for B); record
      throughput / turnaround / waiting / response.
- [ ] @endri  Find optimal (Q1, Q2, L1, L2) and (Q1, Q2, L1, L2, T).
- [ ] @endri  Visualization: heatmaps + 2D + 3D performance surfaces
      (`paper3-scheduling/figures/mlfq/`).

### Queuing models
- [ ] @endri  Implement repeating-forever generator with server rate R/time-unit
      and FCFS postponement of excess.
- [ ] @endri  M/M/1 quantities: ρ, L, Lq, W, Wq, Pn, stability — analytic +
      simulated; cross-check.
- [ ] @endri  M/M/S quantities, same.
- [ ] @endri  Steady-state averages (as t → ∞).
- [ ] @endri  "N, M, R constant over time" sweep; diagrams of quantities and
      probabilities vs M, N, R.
- [ ] @endri  Randomness study: swap distribution (uniform / exponential /
      Poisson); show differences.

### Writing  (5,000–8,000 words, 10–15 pp)
- [ ] @endri  Intro · System model · MLFQ simulation · Metrics ·
      Simulation framework · Optimization study · Visualization ·
      Queuing-theory extension · Randomness study · Results · Conclusion.
- [ ] @endri  Abstract + Keywords + Reproducibility notes.
- [ ] @endri  Appendix: full code, CSVs, raw run dumps.

---

## 4. Final packaging  *(owner: @both)*

- [ ] @both  Assemble the master MS Word report (all 3 papers + all results,
      designs, methodologies, code, screenshots, discussions inline).
- [ ] @both  Collect support files separately: source code, network/data
      files, datasets, raw runs, screenshots, perf-analysis screenshots, plots.
- [ ] @both  Compress into one archive for submission.

---

## 5. Bonus (high-level tier)

- [ ] @both  Push GitHub repo (already in use) — public-ready: README +
      reproduce scripts per paper.
- [ ] @both  Each paper: a "comparison with literature" subsection citing
      prior work.
- [ ] @both  Each paper: a "reproducibility" subsection pointing at
      `ENVIRONMENT.md` + `config/experiments.yaml` + the specific git SHA.
