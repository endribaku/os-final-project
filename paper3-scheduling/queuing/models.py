"""
queuing/models.py
Closed-form (analytic) M/M/1 and M/M/S queueing formulas -- Paper 3 §3.

Conventions
-----------
  lam (lambda) : mean arrival rate     (jobs per time unit)
  mu           : mean service rate of ONE server (jobs per time unit)
  s            : number of identical parallel servers
  rho          : utilization -- lam / mu (M/M/1) or lam / (s*mu) (M/M/S)

Project mapping (Paper 3 §3): N processes arrive within a window of width M, so
the arrival rate is lam = N / M; the system serves up to R processes per time
unit, so the per-server service rate is mu = R.

All quantities follow standard queueing theory (e.g. Silberschatz/Galvin/Gagne,
or any operations-research text). A model with rho >= 1 is unstable: the queue
grows without bound and the steady-state quantities are reported as infinite.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class QueueMetrics:
    """The standard set of steady-state queueing quantities."""

    model: str            # "M/M/1" or "M/M/S"
    lam: float            # arrival rate
    mu: float             # per-server service rate
    servers: int          # s
    rho: float            # utilization
    stable: bool          # rho < 1
    L: float              # mean number in system
    Lq: float             # mean number in queue
    W: float              # mean time in system
    Wq: float             # mean time in queue
    P0: float             # probability the system is empty
    Pw: float             # probability an arrival must wait (Erlang-C; =rho for M/M/1)
    Pn: list[float] = field(default_factory=list)  # P(n in system), n = 0..len-1

    def as_row(self) -> dict:
        """Flatten to a CSV-friendly dict (Pn omitted; it is a vector)."""
        return {
            "model": self.model,
            "lambda": self.lam,
            "mu": self.mu,
            "servers": self.servers,
            "rho": self.rho,
            "stable": self.stable,
            "L": self.L,
            "Lq": self.Lq,
            "W": self.W,
            "Wq": self.Wq,
            "P0": self.P0,
            "Pwait": self.Pw,
        }


def mm1_metrics(lam: float, mu: float, *, n_probs: int = 16) -> QueueMetrics:
    """Steady-state M/M/1 quantities.

    L  = rho / (1 - rho)            Lq = rho^2 / (1 - rho)
    W  = 1 / (mu - lam)             Wq = rho / (mu - lam)
    Pn = (1 - rho) * rho^n
    """
    rho = lam / mu if mu > 0 else math.inf
    stable = rho < 1.0

    if not stable:
        return QueueMetrics(
            model="M/M/1", lam=lam, mu=mu, servers=1, rho=rho, stable=False,
            L=math.inf, Lq=math.inf, W=math.inf, Wq=math.inf,
            P0=0.0, Pw=1.0, Pn=[],
        )

    L = rho / (1.0 - rho)
    Lq = rho * rho / (1.0 - rho)
    W = 1.0 / (mu - lam)
    Wq = rho / (mu - lam)
    P0 = 1.0 - rho
    Pn = [(1.0 - rho) * rho ** n for n in range(n_probs)]

    return QueueMetrics(
        model="M/M/1", lam=lam, mu=mu, servers=1, rho=rho, stable=True,
        L=L, Lq=Lq, W=W, Wq=Wq, P0=P0, Pw=rho, Pn=Pn,
    )


def mms_metrics(lam: float, mu: float, s: int, *, n_probs: int = 16) -> QueueMetrics:
    """Steady-state M/M/S quantities (s identical servers).

    a   = lam / mu  (offered load in Erlangs)
    rho = a / s
    P0  = [ sum_{n=0}^{s-1} a^n/n!  +  a^s / (s! (1-rho)) ]^-1
    Lq  = P0 * a^s * rho / (s! (1-rho)^2)            (Erlang-C derived)
    Wq  = Lq / lam      W = Wq + 1/mu      L = lam * W
    Pw  = P0 * a^s / (s! (1-rho))          (Erlang-C: P[wait > 0])
    """
    if s == 1:
        m = mm1_metrics(lam, mu, n_probs=n_probs)
        m.model = "M/M/S"
        return m

    a = lam / mu if mu > 0 else math.inf
    rho = a / s
    stable = rho < 1.0

    if not stable:
        return QueueMetrics(
            model="M/M/S", lam=lam, mu=mu, servers=s, rho=rho, stable=False,
            L=math.inf, Lq=math.inf, W=math.inf, Wq=math.inf,
            P0=0.0, Pw=1.0, Pn=[],
        )

    # P0 from the normalization sum.
    head = sum(a ** n / math.factorial(n) for n in range(s))
    tail = a ** s / (math.factorial(s) * (1.0 - rho))
    P0 = 1.0 / (head + tail)

    Pw = (a ** s / (math.factorial(s) * (1.0 - rho))) * P0   # Erlang-C
    Lq = Pw * rho / (1.0 - rho)
    Wq = Lq / lam if lam > 0 else 0.0
    W = Wq + 1.0 / mu
    L = lam * W

    # State probabilities P(n in system).
    Pn = []
    for n in range(n_probs):
        if n < s:
            Pn.append(a ** n / math.factorial(n) * P0)
        else:
            Pn.append(a ** n / (math.factorial(s) * s ** (n - s)) * P0)

    return QueueMetrics(
        model="M/M/S", lam=lam, mu=mu, servers=s, rho=rho, stable=True,
        L=L, Lq=Lq, W=W, Wq=Wq, P0=P0, Pw=Pw, Pn=Pn,
    )
