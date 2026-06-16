"""
queuing/simulation.py
Discrete-event simulator for an s-server FCFS queue (Paper 3 §3).

Purpose
-------
1. Cross-check the closed-form M/M/1 / M/M/S formulas in `models.py`: with
   exponential inter-arrival and service times the simulated W, Wq, L, Lq must
   converge to the analytic values.
2. Drive the randomness study: swap the inter-arrival or service distribution
   (uniform / poisson, see `distributions.py`) -- which makes the system a
   G/G/s queue with no simple closed form -- and measure how the quantities
   shift away from the M/M baseline.

Method
------
Customers are generated in arrival order; each is dispatched FCFS to whichever
of the s servers becomes free earliest (exact for FCFS). Per-customer sojourn
and wait times are recorded. After discarding a warm-up prefix:

    W   = mean sojourn time            Wq  = mean queue wait
    L   = (sum of sojourn times) / T   Lq  = (sum of queue waits) / T

using the identity  integral(N dt) = sum(sojourn times)  over the window T.
"""
from __future__ import annotations

import random
import statistics as st
from dataclasses import dataclass

from .distributions import sampler


@dataclass
class SimResult:
    """Measured queueing quantities from one simulation run."""

    model: str
    servers: int
    lam: float
    mu: float
    rho: float
    arrival_dist: str
    service_dist: str
    n_measured: int
    L: float
    Lq: float
    W: float
    Wq: float
    server_utilization: float

    def as_row(self) -> dict:
        return {
            "model": self.model,
            "servers": self.servers,
            "lambda": self.lam,
            "mu": self.mu,
            "rho": self.rho,
            "arrival_dist": self.arrival_dist,
            "service_dist": self.service_dist,
            "n_measured": self.n_measured,
            "L": self.L,
            "Lq": self.Lq,
            "W": self.W,
            "Wq": self.Wq,
            "server_utilization": self.server_utilization,
        }


def simulate_queue(
    lam: float,
    mu: float,
    *,
    servers: int = 1,
    n_arrivals: int = 100_000,
    warmup: int = 5_000,
    arrival_dist: str = "exponential",
    service_dist: str = "exponential",
    rng: random.Random | None = None,
) -> SimResult:
    """Simulate an s-server FCFS queue and return its measured quantities.

    Parameters
    ----------
    lam, mu      : arrival rate and per-server service rate.
    servers      : number of identical parallel servers (s).
    n_arrivals   : total customers to simulate (-> infinity as it grows).
    warmup       : leading customers discarded before measuring steady state.
    arrival_dist : distribution of inter-arrival times (mean held at 1/lam).
    service_dist : distribution of service times       (mean held at 1/mu).
    rng          : seeded random.Random for reproducibility.
    """
    rng = rng or random.Random()
    draw_gap = sampler(arrival_dist)
    draw_svc = sampler(service_dist)
    mean_gap = 1.0 / lam
    mean_svc = 1.0 / mu

    free_at = [0.0] * servers          # when each server next becomes free
    clock = 0.0                        # running arrival clock
    busy_area = 0.0                    # integral of (#busy servers) dt -- crude

    sojourns: list[float] = []         # W_i for measured customers
    waits: list[float] = []            # Wq_i for measured customers
    first_arrival = last_departure = None

    for i in range(n_arrivals):
        clock += draw_gap(mean_gap, rng)
        arrival = clock

        # Dispatch FCFS to the earliest-free server.
        srv = min(range(servers), key=lambda k: free_at[k])
        service_start = max(arrival, free_at[srv])
        service_time = draw_svc(mean_svc, rng)
        departure = service_start + service_time
        free_at[srv] = departure

        if i >= warmup:
            wq = service_start - arrival
            w = departure - arrival
            waits.append(wq)
            sojourns.append(w)
            busy_area += service_time
            if first_arrival is None:
                first_arrival = arrival
            last_departure = departure

    n = len(sojourns)
    rho = lam / (servers * mu)
    if n == 0 or first_arrival is None:
        return SimResult(
            model=f"M/M/{servers}" if servers > 1 else "M/M/1",
            servers=servers, lam=lam, mu=mu, rho=rho,
            arrival_dist=arrival_dist, service_dist=service_dist,
            n_measured=0, L=0.0, Lq=0.0, W=0.0, Wq=0.0, server_utilization=0.0,
        )

    window = last_departure - first_arrival
    return SimResult(
        model=f"M/M/{servers}" if servers > 1 else "M/M/1",
        servers=servers, lam=lam, mu=mu, rho=rho,
        arrival_dist=arrival_dist, service_dist=service_dist,
        n_measured=n,
        W=st.fmean(sojourns),
        Wq=st.fmean(waits),
        L=sum(sojourns) / window if window > 0 else 0.0,
        Lq=sum(waits) / window if window > 0 else 0.0,
        server_utilization=busy_area / (servers * window) if window > 0 else 0.0,
    )
