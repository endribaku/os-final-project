"""
mlfq/process.py
Process model and the random workload generator for the MLFQ simulator.

The project (Paper 3 §2) specifies:
  - N processes,
  - random burst times in [10, 1000] time units,
  - random arrival moments in [0, M] time units, with M << N.

`generate_processes` produces exactly that. The arrival distribution is
selectable so the Paper 3 "randomness study" can swap uniform <-> exponential
<-> poisson without touching the simulator.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

# Burst-time range fixed by the project statement.
DEFAULT_BURST_RANGE: tuple[int, int] = (10, 1000)


@dataclass
class Process:
    """A single process: immutable inputs plus mutable simulation state.

    Inputs (set at creation):
        pid           -- unique id.
        arrival_time  -- when the process enters the system.
        burst_time    -- total CPU time the process needs.

    Simulation state (mutated by the scheduler):
        remaining        -- CPU time still required.
        level            -- current queue level (0, 1 or 2).
        start_time       -- clock at first dispatch (None until first run).
        completion_time  -- clock at completion (None until finished).
    """

    pid: int
    arrival_time: float
    burst_time: int

    remaining: float = field(init=False)
    level: int = field(default=0)
    start_time: float | None = field(default=None)
    completion_time: float | None = field(default=None)

    def __post_init__(self) -> None:
        self.remaining = float(self.burst_time)

    @property
    def finished(self) -> bool:
        return self.completion_time is not None

    # --- per-process metrics (valid only after completion) -------------------
    @property
    def turnaround(self) -> float:
        """Completion - arrival."""
        return self.completion_time - self.arrival_time

    @property
    def waiting(self) -> float:
        """Turnaround - burst (time spent not running)."""
        return self.turnaround - self.burst_time

    @property
    def response(self) -> float:
        """First-dispatch - arrival."""
        return self.start_time - self.arrival_time


def generate_processes(
    n: int,
    m: float,
    *,
    burst_range: tuple[int, int] = DEFAULT_BURST_RANGE,
    arrival_dist: str = "uniform",
    rng: random.Random | None = None,
) -> list[Process]:
    """Generate `n` processes arriving within the window [0, m].

    Parameters
    ----------
    n            : number of processes.
    m            : width of the arrival window (M in the project statement).
    burst_range  : inclusive [lo, hi] range for the uniform random burst time.
    arrival_dist : "uniform" | "exponential" | "poisson" -- how arrival
                   instants are drawn within [0, m]. "uniform" is the project
                   default; the others feed the randomness study.
    rng          : a seeded random.Random for reproducibility.

    Returns the processes sorted by arrival_time.
    """
    rng = rng or random.Random()
    lo, hi = burst_range
    procs: list[Process] = []

    for pid in range(n):
        burst = rng.randint(lo, hi)
        arrival = _draw_arrival(arrival_dist, m, rng)
        procs.append(Process(pid=pid, arrival_time=arrival, burst_time=burst))

    procs.sort(key=lambda p: p.arrival_time)
    return procs


def _draw_arrival(dist: str, m: float, rng: random.Random) -> float:
    """Draw a single arrival instant in [0, m] under the named distribution."""
    if dist == "uniform":
        return rng.uniform(0.0, m)
    if dist == "exponential":
        # Exponential clipped to the window; mean placed at m/2.
        return min(rng.expovariate(2.0 / m), m)
    if dist == "poisson":
        # Poisson count scaled into the window (discrete-ish arrival instant).
        # Uses a unit-mean Poisson draw mapped onto [0, m].
        k = _poisson(1.0, rng)
        return min(k / 2.0 * m, m)
    raise ValueError(f"unknown arrival_dist: {dist!r}")


def _poisson(lam: float, rng: random.Random) -> int:
    """Knuth's algorithm for a Poisson(lam) variate (no numpy dependency)."""
    import math

    el = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= el:
            return k - 1
