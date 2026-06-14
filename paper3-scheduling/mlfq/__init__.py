"""
paper3-scheduling / mlfq
========================

Discrete-event simulator for the three-level Multilevel Feedback Queue (MLFQ)
studied in Paper 3 §2. Public surface:

    from mlfq import Process, generate_processes
    from mlfq import MLFQConfig, MLFQSimulator, simulate
    from mlfq import summarize

See `simulator.py` for the scheduling model and the documented modelling
assumptions (duty-cycle interpretation of the level allotments L1/L2/L3).
"""
from __future__ import annotations

from .process import Process, generate_processes
from .simulator import MLFQConfig, MLFQSimulator, simulate
from .metrics import summarize

__all__ = [
    "Process",
    "generate_processes",
    "MLFQConfig",
    "MLFQSimulator",
    "simulate",
    "summarize",
]
