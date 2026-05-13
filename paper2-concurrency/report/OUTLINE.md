# Paper 2 — Outline

**Title:** Comparative Performance Evaluation of Multithreaded Synchronization
Techniques in Producer–Consumer and Dining Philosophers Problems

**Format:** 10 pt, one-column, single-spaced, 10–15 pages, 5,000–8,000 words.
Appendices don't count toward the page/word limit.

**File:** `paper2.docx` (in this folder).

---

## Front matter
- Title, authors, affiliation, date
- **Abstract** (~200 words)
- **Keywords** (5–8)

## Body sections (doc-prescribed outline)

1. **Introduction**
   - Synchronization challenges
   - Relevance in multicore systems

2. **Related Work**
   - Classical problems (producer–consumer, dining philosophers)
   - Mutexes, semaphores, monitors

3. **Methodology**
   - 3.1 Producer–Consumer (bounded buffer)
     - POSIX Threads implementation
     - Java implementation
   - 3.2 Dining Philosophers
     - Monitor-based (lecture solution)
     - Semaphore-based
     - Resource-hierarchy
     - POSIX Threads + Java implementations

4. **Experimental Design**
   - Variables: N (buffer), M (producers), K (consumers), P (philosophers)
   - Metrics: throughput, latency, context switches, CPU usage, deadlock frequency
   - Reference `config/experiments.yaml`

5. **Performance Evaluation**
   - Graphs: time vs threads, CPU vs contention
   - Stress tests

6. **Scalability Study**
   - Producer–Consumer → M × K threads
   - Philosophers → N nodes

7. **Comparative Analysis**
   - POSIX vs Java
   - Locks vs monitors vs semaphores

8. **Optimization Proposal**
   - Lock-free ideas
   - Adaptive buffer sizing
   - (Optional) prototype + benchmark

9. **Discussion**

10. **Conclusion**

## Back matter
- **Reproducibility notes** — cite `ENVIRONMENT.md` + `config/experiments.yaml` + git SHA + bench commands
- **References** — Baeldung article, UCSB DiningPhil testbed, lecture slides, any compared literature (bonus)
- **Appendices** *(not counted toward page/word limit)*
  - A. Full source code (pthreads + Java, both problems, all DP algorithms)
  - B. Sweep driver scripts
  - C. Raw benchmark logs
  - D. All plots (full resolution)
