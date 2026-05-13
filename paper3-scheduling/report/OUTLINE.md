# Paper 3 — Outline

**Title:** Optimization of Multilevel Feedback Queue Scheduling and Queueing
Models Using Simulation and Analytical Techniques

**Format:** 10 pt, one-column, single-spaced, 10–15 pages, 5,000–8,000 words.
Appendices don't count toward the page/word limit.

**File:** `paper3.docx` (in this folder).

---

## Front matter
- Title, authors, affiliation, date
- **Abstract** (~200 words)
- **Keywords** (5–8)

## Body sections (doc-prescribed outline)

1. **Introduction**
   - Scheduling importance
   - Limitations of default RR quantum values

2. **System Model**
   - Processes: burst time random in [10, 1000]; arrivals stochastic over [0, M]
   - 3-level feedback queue: Q0 = RR(Q1), Q1 = RR(Q2), Q2 = FCFS
   - Level allotments L1, L2, L3 = 100 − L1 − L2

3. **MLFQ Simulation**
   - Parameters: Q1, Q2 (quanta); L1, L2 (allotments); T (SJF vs FCFS split, variant B)
   - Both variants A and B

4. **Metrics**
   - Throughput · turnaround time · waiting time · response time

5. **Simulation Framework**
   - Python implementation
   - Monte Carlo runs (100–500 trials; we use 300)
   - Reference `config/experiments.yaml`

6. **Optimization Study**
   - Grid search over Q1, Q2, L1, L2 (and T for variant B)
   - Statistical averaging
   - Optimal values identified per metric

7. **Visualization**
   - Heatmaps
   - 2D / 3D performance surfaces

8. **Queuing Theory Extension**
   - M/M/1 quantities (ρ, L, Lq, W, Wq, Pn, stability)
   - M/M/S quantities
   - Steady-state (t → ∞) + N, M, R constant cases
   - Server rate R + FCFS postponement of excess

9. **Randomness Study**
   - Uniform vs exponential vs Poisson
   - Differences in resulting quantities

10. **Results**
    - Tables, plots, surfaces, heatmaps

11. **Conclusion**
    - Publishable contribution: empirical + analytical optimization of MLFQ
      integrated with queueing theory

## Back matter
- **Reproducibility notes** — cite `ENVIRONMENT.md` + `config/experiments.yaml` + git SHA + grid-search script paths + RNG seeds
- **References** — Silberschatz/Galvin/Gagne (textbook), queueing-theory references, MLFQ tuning literature (bonus)
- **Appendices** *(not counted toward page/word limit)*
  - A. Full source: MLFQ simulator (A + B), grid search, M/M/1 + M/M/S models
  - B. All CSVs from Monte Carlo runs
  - C. All plots (full resolution)
  - D. Analytical derivations (if any) for M/M/S formulas
