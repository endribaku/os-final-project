"""
mlfq/simulator.py
Three-level Multilevel Feedback Queue scheduler (Paper 3 §2, variants A and B).

Scheduling model
----------------
Three queues, levels 0, 1, 2:
  - Level 0: Round-Robin with time quantum Q1.
  - Level 1: Round-Robin with time quantum Q2.
  - Level 2: FCFS                (variant A)
             SJF for T% then FCFS (variant B).

Level allotments L1, L2, L3 -- the duty-cycle interpretation
------------------------------------------------------------
The project says: "if we assume 100 ms of time, the first level should run for
L1, the second for L2 and the third one for 100-L1-L2." Because process bursts
range up to 1000 time units while L1+L2+L3 = 100, the L_i values CANNOT be
per-process CPU allotments (100 units could never finish a 1000-unit burst).
They are therefore read as a **scheduler duty cycle**: the CPU repeatedly
cycles through a 100-unit super-cycle, spending L1 units servicing level 0,
then L2 servicing level 1, then L3 = 100-L1-L2 servicing level 2.

Demotion rule
-------------
Standard MLFQ: a process that consumes a *full* time quantum at level 0 or 1
without finishing is demoted one level. A process preempted only because its
duty-cycle phase ended (it ran for less than a full quantum) is NOT demoted --
it is requeued at the same level. New arrivals always enter level 0.

Empty-phase policy
------------------
If the queue for the current phase is empty, the phase ends early (the
scheduler does not idle-spin through an empty phase). When the whole system is
idle but more arrivals are pending, the clock fast-forwards to the next
arrival. Both choices are configurable via `MLFQConfig`.

All of the above is a documented modelling decision; if the course expects a
different reading of L1/L2/L3, only this file needs to change.
"""
from __future__ import annotations

import heapq
import math
from collections import deque
from dataclasses import dataclass

from .process import Process

_EPS = 1e-9


@dataclass
class MLFQConfig:
    """Tunable scheduler parameters -- the knobs the grid search optimizes."""

    q1: int                 # Round-Robin quantum at level 0
    q2: int                 # Round-Robin quantum at level 1
    l1: int                 # duty-cycle budget for level 0
    l2: int                 # duty-cycle budget for level 1
    cycle: int = 100        # total super-cycle length; l3 = cycle - l1 - l2
    variant: str = "A"      # "A" = level-2 pure FCFS; "B" = SJF split then FCFS
    t_split: int = 0        # variant B only: % of L3 budget given to SJF first
    idle_through_empty_phase: bool = False  # if True, honour L_i even when idle

    @property
    def l3(self) -> int:
        """Derived level-2 budget."""
        return self.cycle - self.l1 - self.l2

    def is_valid(self) -> bool:
        """A config is usable only if every level gets a positive budget."""
        return (
            self.q1 > 0
            and self.q2 > 0
            and self.l1 > 0
            and self.l2 > 0
            and self.l3 > 0
            and self.variant in ("A", "B")
            and 0 <= self.t_split <= 100
        )


class MLFQSimulator:
    """Event-stepped MLFQ simulator. One instance simulates one process list."""

    def __init__(self, processes: list[Process], config: MLFQConfig):
        if not config.is_valid():
            raise ValueError(f"invalid MLFQConfig: {config}")
        self.cfg = config
        # Processes sorted by arrival; the simulator mutates their state.
        self.procs: list[Process] = sorted(processes, key=lambda p: p.arrival_time)
        self.n = len(self.procs)
        self.clock = 0.0
        self.completed = 0
        self._next_idx = 0                      # next un-admitted arrival
        self.queues: list[deque[Process]] = [deque(), deque(), deque()]
        self.context_switches = 0               # dispatch count (a proxy metric)

    # -- internals ------------------------------------------------------------
    def _admit(self) -> None:
        """Move every process that has arrived by `clock` into level-0 queue."""
        while (
            self._next_idx < self.n
            and self.procs[self._next_idx].arrival_time <= self.clock + _EPS
        ):
            self.queues[0].append(self.procs[self._next_idx])
            self._next_idx += 1

    def _all_queues_empty(self) -> bool:
        return not (self.queues[0] or self.queues[1] or self.queues[2])

    def _quantum(self, level: int) -> float:
        return (self.cfg.q1, self.cfg.q2, math.inf)[level]

    # -- main loop ------------------------------------------------------------
    def run(self) -> list[Process]:
        """Run the simulation to completion; returns the (mutated) processes."""
        while self.completed < self.n:
            self._admit()
            if self._all_queues_empty():
                if self._next_idx < self.n:
                    # CPU idle: fast-forward to the next arrival.
                    self.clock = max(
                        self.clock, self.procs[self._next_idx].arrival_time
                    )
                    self._admit()
                else:
                    break  # safety: nothing ready and nothing pending
            for level in range(3):
                self._run_phase(level)
        return self.procs

    def _run_phase(self, level: int) -> None:
        """Service `level` for its duty-cycle budget (one super-cycle phase)."""
        budget = (self.cfg.l1, self.cfg.l2, self.cfg.l3)[level]
        if budget <= 0:
            return
        target = self.clock + budget

        if level == 2 and self.cfg.variant == "B" and self.cfg.t_split > 0:
            # Variant B: split the level-2 budget -- SJF first, then FCFS.
            sjf_target = self.clock + budget * self.cfg.t_split / 100.0
            self._serve_sjf(sjf_target)
            self._serve(level, target)
        else:
            self._serve(level, target)

    def _serve(self, level: int, target: float) -> None:
        """Service queue `level` (RR or FCFS) until `clock` reaches `target`.

        Levels 0 and 1 are Round-Robin (finite quantum -> demotion on full
        use); level 2 is FCFS (infinite quantum). Both dispatch from the head
        of the queue, so no policy flag is needed.
        """
        q = self.queues[level]
        quantum = self._quantum(level)

        while self.clock < target - _EPS:
            self._admit()
            if not q:
                if self.cfg.idle_through_empty_phase and not self._all_queues_empty():
                    # Honour L_i strictly: burn the rest of the phase idle.
                    self.clock = target
                return  # default: end the phase early

            proc = q.popleft()
            if proc.start_time is None:
                proc.start_time = self.clock

            time_left = target - self.clock
            slice_ = min(proc.remaining, quantum, time_left)
            self.clock += slice_
            proc.remaining -= slice_
            self.context_switches += 1
            self._admit()  # arrivals during the slice

            if proc.remaining <= _EPS:
                proc.completion_time = self.clock
                self.completed += 1
            elif quantum != math.inf and slice_ >= quantum - _EPS:
                # Full quantum used without finishing -> demote one level.
                proc.level = min(level + 1, 2)
                self.queues[proc.level].append(proc)
            else:
                # Preempted only by the phase boundary -> requeue, same level.
                q.append(proc)

    def _serve_sjf(self, target: float) -> None:
        """Service level 2 Shortest-Job-First until `clock` reaches `target`.

        Uses a binary min-heap keyed on remaining time, so each dispatch is
        O(log n). The earlier implementation scanned the level-2 queue with
        `min()` plus a list `remove()` -- O(n) per dispatch -- which made the
        whole sub-phase O(n^2) and variant B ~50x slower than variant A under
        a long level-2 queue. Heap entries are (remaining, pid, proc); the pid
        breaks ties so two Process objects are never compared.
        """
        q = self.queues[2]
        # Drain the level-2 queue into a heap ordered by remaining time.
        heap: list[tuple[float, int, Process]] = [
            (p.remaining, p.pid, p) for p in q
        ]
        q.clear()
        heapq.heapify(heap)

        while self.clock < target - _EPS:
            self._admit()  # new arrivals enter level 0; no effect on level 2
            if not heap:
                if self.cfg.idle_through_empty_phase and not self._all_queues_empty():
                    self.clock = target
                break  # default: end the sub-phase early

            _, _, proc = heapq.heappop(heap)
            if proc.start_time is None:
                proc.start_time = self.clock

            time_left = target - self.clock
            slice_ = min(proc.remaining, time_left)  # level 2 -> no quantum
            self.clock += slice_
            proc.remaining -= slice_
            self.context_switches += 1
            self._admit()

            if proc.remaining <= _EPS:
                proc.completion_time = self.clock
                self.completed += 1
            else:
                # Preempted by the SJF sub-phase boundary -> back on the heap.
                heapq.heappush(heap, (proc.remaining, proc.pid, proc))

        # Return any leftover processes to the level-2 queue in arrival order
        # so the following FCFS sub-phase dispatches them correctly.
        for _, _, proc in sorted(heap, key=lambda e: e[2].arrival_time):
            q.append(proc)


def simulate(processes: list[Process], config: MLFQConfig) -> MLFQSimulator:
    """Convenience: build a simulator, run it, return it (for metric access)."""
    sim = MLFQSimulator(processes, config)
    sim.run()
    return sim
