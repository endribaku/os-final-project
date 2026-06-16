"""
queuing/distributions.py
Random samplers for inter-arrival and service times.

The project's "randomness study" (Paper 3 §3) asks: does the choice of random
function change the resulting queueing quantities? Each sampler here draws a
non-negative time with a *given mean*, so swapping the distribution while
holding the mean fixed isolates the effect of the distribution's shape.

  - exponential : the classic M/M assumption (memoryless; CV = 1).
  - uniform     : U(0, 2*mean) -- same mean, bounded support, CV = 1/sqrt(3).
  - poisson     : Poisson(mean) integer draw -- discrete, CV = 1/sqrt(mean).

Note: only `exponential` makes the analytic M/M/1 and M/M/S formulas exact;
`uniform` and `poisson` turn the system into a G/G/* queue and are meant to be
fed to the *simulator* and compared against the M/M baseline.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable

# A sampler maps (mean, rng) -> a single non-negative sample.
Sampler = Callable[[float, random.Random], float]


def _exponential(mean: float, rng: random.Random) -> float:
    return rng.expovariate(1.0 / mean) if mean > 0 else 0.0


def _uniform(mean: float, rng: random.Random) -> float:
    return rng.uniform(0.0, 2.0 * mean)


def _poisson(mean: float, rng: random.Random) -> float:
    """Knuth's Poisson(mean) algorithm, returned as a float time."""
    if mean <= 0:
        return 0.0
    el = math.exp(-mean)
    k = 0
    p = 1.0
    while True:
        k += 1
        p *= rng.random()
        if p <= el:
            return float(k - 1)


DISTRIBUTIONS: dict[str, Sampler] = {
    "exponential": _exponential,
    "uniform": _uniform,
    "poisson": _poisson,
}


def sampler(name: str) -> Sampler:
    """Look up a sampler by name; raises ValueError on an unknown name."""
    try:
        return DISTRIBUTIONS[name]
    except KeyError:
        raise ValueError(
            f"unknown distribution {name!r}; choose from {sorted(DISTRIBUTIONS)}"
        ) from None
