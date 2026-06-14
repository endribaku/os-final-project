"""
drivers/_p3_common.py
Shared plumbing for the Paper 3 drivers (run_mlfq, run_queuing, plot_*).

Handles three things every driver needs:
  1. sys.path wiring so `import mlfq`, `import queuing` and `from common import
     plots` all resolve regardless of the (hyphenated) directory names.
  2. loading config/experiments.yaml.
  3. an append-only CSV writer whose header is materialised from the first row.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

# paper3-scheduling/  -> for `import mlfq`, `import queuing`
PAPER3_DIR = Path(__file__).resolve().parents[1]
# repo root           -> for `from common import plots`
ROOT = Path(__file__).resolve().parents[2]
for _p in (str(PAPER3_DIR), str(ROOT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import yaml  # noqa: E402

RESULTS_DIR = PAPER3_DIR / "results"
FIGURES_DIR = PAPER3_DIR / "figures"


def load_cfg() -> dict:
    """Parse config/experiments.yaml from the repo root."""
    return yaml.safe_load((ROOT / "config" / "experiments.yaml").read_text())


def paper3_cfg() -> dict:
    """Just the `paper3:` block of the config."""
    return load_cfg()["paper3"]


def global_seeds() -> list[int]:
    """The shared RNG seed list (global.seeds in the config)."""
    return load_cfg()["global"]["seeds"]


class CsvSink:
    """Append-only CSV writer; header taken from the first row's keys.

    Later rows are written with extrasaction='ignore', so a row with a slightly
    different field set does not abort the run.
    """

    def __init__(self, out_path: Path):
        self.path = Path(out_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._f = None
        self._writer: csv.DictWriter | None = None

    def write(self, row: dict) -> None:
        if self._writer is None:
            is_new = not (self.path.exists() and self.path.stat().st_size > 0)
            self._f = self.path.open("a", newline="")
            self._writer = csv.DictWriter(
                self._f, fieldnames=list(row.keys()), extrasaction="ignore"
            )
            if is_new:
                self._writer.writeheader()
        self._writer.writerow(row)

    def close(self) -> None:
        if self._f:
            self._f.close()

    def __enter__(self) -> "CsvSink":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
