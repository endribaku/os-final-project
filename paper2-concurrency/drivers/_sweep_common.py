"""
Shared helpers for sweep_pc.py and sweep_dp.py.

Both drivers do the same skeleton:
    1. Load config/experiments.yaml.
    2. Iterate a parameter grid.
    3. For each (config, seed/rep) run the binary under common.bench.run.
    4. Parse the JSON line emitted on the binary's stdout.
    5. Merge {bench_metrics, app_metrics, sweep_meta} into one CSV row.

The differences between the two are the grid and how seed/reps map onto runs,
so the small per-driver scripts contain just those pieces.
"""
from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Iterable

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))  # so `from common import bench` works
from common import bench  # noqa: E402


def load_cfg() -> dict:
    return yaml.safe_load((ROOT / "config" / "experiments.yaml").read_text())


def parse_json_line(stdout: str) -> dict | None:
    """Return the parsed last non-empty JSON line on stdout, or None."""
    if not stdout:
        return None
    for line in reversed(stdout.strip().splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


class CsvSink:
    """Append-only CSV writer that materialises the header from the first row.

    Subsequent rows are written with extrasaction='ignore' so a slightly
    different field set (e.g. extra warmup column) doesn't blow up the run.
    """

    def __init__(self, out_path: Path):
        self.path = out_path
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


def make_row(br: bench.BenchResult, app: dict, **meta) -> dict:
    """Combine bench fields + app JSON + arbitrary sweep metadata into one row."""
    row = asdict(br)
    row.pop("stdout", None)
    row.pop("stderr", None)
    row.update(app)
    row.update(meta)
    return row


def run_one(cmd: str, repetitions: int, *, label: str = "", dry: bool = False
            ) -> Iterable[bench.BenchResult]:
    """Run `cmd` `repetitions` times under bench.run. If dry, just print and skip."""
    if label:
        print(f"[run] {label}: {cmd}  (reps={repetitions})", file=sys.stderr)
    else:
        print(f"[run] {cmd}  (reps={repetitions})", file=sys.stderr)
    if dry:
        return []
    return bench.run(cmd, repetitions=repetitions)
