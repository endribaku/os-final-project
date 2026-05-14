# Paper 2 §8 — Optimization Proposal

The doc asks for two things under "Optimization Proposal":

1. **Lock-free ideas** — implemented as a working prototype, see below.
2. **Adaptive buffer sizing** — discussed as future work.

This file documents the proposal, where the code lives, how to run it,
and what we expect to see when comparing it against the baseline monitor
implementation.

---

## 1. Lock-free MPMC bounded ring buffer (implemented)

**Code:** [`pc/java/ProducerConsumerLockFree.java`](pc/java/ProducerConsumerLockFree.java).

### Algorithm

A Vyukov-style multi-producer / multi-consumer bounded ring buffer
(Vyukov, "Bounded MPMC queue", 1024cores.net):

- Capacity `N` is rounded up to the next power of two so the cell index
  reduces to `pos & mask`.
- Each cell carries a 64-bit `sequence` counter alongside the payload.
  Initially, cell `i` has `sequence = i`.
- The producer side advances a global `enqueuePos`; the consumer side
  advances `dequeuePos`. Both updates are CAS-only — no mutexes, no
  condition variables, no semaphores.
- A producer succeeds when it observes `cell.sequence == pos` (the slot is
  free at its turn); it then CAS-bumps `enqueuePos`, writes the value, and
  publishes by setting `cell.sequence = pos + 1`.
- A consumer succeeds when it observes `cell.sequence == pos + 1` (a
  freshly published value); it CAS-bumps `dequeuePos`, reads, and "frees"
  the slot by setting `cell.sequence = pos + capacity`.
- When the queue is full or empty, `tryEnqueue` / `tryDequeue` return
  immediately. Callers handle back-off with `Thread.onSpinWait()` — the
  whole implementation is non-blocking by construction.

### Why this is the right comparison axis

Paper 2 §7 explicitly asks to compare "locks vs monitors or semaphores vs
mutexes". The existing implementations cover **monitor** (`ProducerConsumer.java`),
**mutex + two semaphores** (`pc/pthreads/producer_consumer.c`) and three
DP variants. The lock-free queue contributes the missing axis: **the same
problem with zero kernel-blocking synchronisation primitives.**

### Predicted behaviour vs the monitor baseline

| Metric                 | Direction              | Why |
|---|---|---|
| Throughput             | ↑ at high contention   | No syscall round-trip for `wait`/`notify` |
| p50 latency            | ↑ at high contention   | No condition-variable wakeup cost |
| p99 latency            | ↑                      | No "thundering herd" on `notifyAll` |
| CPU %                  | ↑                      | Busy-spin keeps cores hot when the queue is empty/full |
| Voluntary ctx switches | ↓ sharply              | Threads never enter the kernel waiting on a lock |
| Throughput at low M/K  | ≈                      | Light contention -> monitor's `wait` rarely fires anyway |
| Wall time, long runs   | ↓ at high contention; ≈ at low contention | Same throughput story integrated over time |

The empirical question for the paper is **where the curves cross** in
throughput-vs-thread-count and CPU-vs-thread-count.

### Build & run

Same CLI as the monitor variant — the sweep driver and plot scripts
treat both uniformly:

```bash
# in the VM
cd paper2-concurrency/pc/java
javac ProducerConsumerLockFree.java
java ProducerConsumerLockFree --N 64 --M 4 --K 4 --items 10000

# included in the sweep automatically:
PYTHONPATH=. python paper2-concurrency/drivers/sweep_pc.py
PYTHONPATH=. python paper2-concurrency/drivers/plot_pc.py
```

`sweep_pc.py` already lists `java-lockfree` in its `IMPLS` table, and
[`_plot_common.py`](drivers/_plot_common.py) gives it its own line colour
and legend label (green) so every PC figure will show three lines —
Java monitor, Java lock-free, C pthreads-with-mutex — for the
"locks vs monitors vs lock-free" comparison.

### Caveats / honest limitations

- **Capacity is a power of two, and ≥ 2.** If you pass `--N 50` the queue
  rounds up to 64; if you pass `--N 1` it clamps to 2. With capacity 1
  the Vyukov sequence-number scheme degenerates — post-enqueue and
  post-dequeue sequence values for the single slot become equal, which
  lets a producer race past a still-unread value. The other PC variants
  (monitor + pthreads) DO honour N=1 verbatim, so a head-to-head
  comparison at N=1 is still meaningful; the lock-free row at that point
  uses `effective_N: 2`.
- **Busy-spin uses CPU.** When the queue is empty or full the spinning
  threads stay on-CPU. `Thread.onSpinWait()` (Java 9+) softens this, but
  the lock-free variant is expected to draw more CPU at low concurrency.
- **The JMM ordering relies on `AtomicLong` get/set acting as
  acquire/release** through the cell-sequence chain. We've kept the
  publication order conservative (set the value, then set the sequence,
  always paired with a CAS).
- **Only Java for the prototype.** A C/`<stdatomic.h>` port is a natural
  extension and is mentioned in the paper's "future work".

---

## 2. Adaptive buffer sizing (future work)

The motivation: a fixed `N` is a tuning parameter the user has to guess.
Too small -> producers stall; too large -> wasted memory and worse cache
behaviour. The doc proposes letting the queue **resize itself based on
observed contention.**

### Sketched design

- Maintain a moving average of the `tryEnqueue`-returned-false rate
  (i.e. "buffer was full") and the `tryDequeue`-returned-empty rate.
- Every `T` ms, the policy thread reads both EMAs:
  - if `full_rate > θ_high` -> grow `N` (e.g. ×2, capped at `N_max`)
  - if both rates `< θ_low`  -> shrink `N` (e.g. /2, floored at `N_min`)
- Resizing is non-trivial because the ring buffer is fixed-capacity. Two
  workable patterns:
  1. **Snapshot resize**: at a quiescent point, allocate a new ring of
     the target capacity and migrate. Easy correctness, brief stall.
  2. **Chunked queue**: keep a linked list of fixed-size segments;
     allocate a new segment when one fills, recycle when one empties.
     No global resize event but more cache pressure.

### Why we deferred it

The proposal is conceptually clean but the experimental contribution
overlaps heavily with the existing N-sweep figures: `plot_pc.py` already
shows throughput-vs-N curves, which lets readers pick the "right" `N` for
any (M, K) load. An adaptive scheme essentially traces those curves at
runtime. Producing a publishable result on top would require:

- A workload mix (varying M, K, delays) so the right `N` actually changes
  during one run, otherwise the adaptive scheme is just slow.
- Comparing convergence time and steady-state overhead against the fixed-`N`
  optimum.

Both are well-scoped follow-ups; the lock-free prototype + the regular
sweep already provide enough quantitative material for §8 of Paper 2.

---

## What goes in the paper

§8 should be ~1 page and contain:

1. Motivation (one paragraph) — kernel-blocking synchronisation costs;
   the Coffman / contention story from §5–§7.
2. Algorithm description — the Vyukov queue (1/2 page, the algorithm box
   above, citing 1024cores).
3. Experimental comparison — one or two figures from `figures/pc/` that
   already include `java-lockfree` (throughput-vs-(M+K), CPU-vs-contention,
   ctxsw-vs-threads). Reference the comparative bar panel.
4. Trade-offs — busy-spin CPU cost vs ctxsw / latency wins.
5. Adaptive-buffer paragraph as future work.
