"""
paper3-scheduling / queuing
===========================

Queueing-theory models for Paper 3 §3. Public surface:

    from queuing import mm1_metrics, mms_metrics, QueueMetrics
    from queuing import simulate_queue
    from queuing import sampler, DISTRIBUTIONS

`models.py` holds the closed-form M/M/1 and M/M/S formulas; `simulation.py`
holds a discrete-event simulator used to cross-check the analytic results and
to run the "randomness study" (swap the inter-arrival / service distribution).
"""
from __future__ import annotations

from .distributions import DISTRIBUTIONS, sampler
from .models import QueueMetrics, mm1_metrics, mms_metrics
from .simulation import simulate_queue

__all__ = [
    "QueueMetrics",
    "mm1_metrics",
    "mms_metrics",
    "simulate_queue",
    "sampler",
    "DISTRIBUTIONS",
]
