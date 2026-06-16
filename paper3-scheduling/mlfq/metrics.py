"""
mlfq/metrics.py
Aggregate the four scheduling metrics the project asks to optimize:

    throughput   -- completions per time unit  (maximize)
    turnaround   -- completion - arrival       (minimize)
    waiting      -- turnaround - burst         (minimize)
    response     -- first dispatch - arrival   (minimize)

`summarize` takes the processes returned by a finished MLFQSimulator and
returns a flat dict of means, ready to become one CSV row.
"""
from __future__ import annotations

import statistics as st
from collections.abc import Iterable

from .process import Process


def summarize(processes: Iterable[Process], context_switches: int | None = None) -> dict:
    """Reduce a finished process list to a flat metrics dict.

    Throughput is completions divided by the makespan (the clock at the last
    completion), i.e. system-wide jobs-per-time-unit.
    """
    finished = [p for p in processes if p.finished]
    n = len(finished)
    if n == 0:
        return {
            "n_completed": 0,
            "throughput": 0.0,
            "turnaround_mean": 0.0,
            "waiting_mean": 0.0,
            "response_mean": 0.0,
            "turnaround_p95": 0.0,
            "waiting_p95": 0.0,
            "makespan": 0.0,
            "context_switches": context_switches or 0,
        }

    turnaround = [p.turnaround for p in finished]
    waiting = [p.waiting for p in finished]
    response = [p.response for p in finished]
    makespan = max(p.completion_time for p in finished)

    return {
        "n_completed": n,
        "throughput": n / makespan if makespan > 0 else 0.0,
        "turnaround_mean": st.fmean(turnaround),
        "waiting_mean": st.fmean(waiting),
        "response_mean": st.fmean(response),
        "turnaround_p95": _percentile(turnaround, 95),
        "waiting_p95": _percentile(waiting, 95),
        "makespan": makespan,
        "context_switches": context_switches if context_switches is not None else 0,
    }


def mean_of(rows: list[dict], key: str) -> float:
    """Mean of `key` across a list of metric dicts (Monte Carlo averaging)."""
    vals = [r[key] for r in rows if key in r]
    return st.fmean(vals) if vals else 0.0


def _percentile(values: list[float], pct: float) -> float:
    """Simple nearest-rank percentile (no numpy dependency)."""
    if not values:
        return 0.0
    ordered = sorted(values)
    k = max(0, min(len(ordered) - 1, round(pct / 100.0 * len(ordered)) - 1))
    return ordered[k]
