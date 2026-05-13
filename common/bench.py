"""
common/bench.py
Performance-measurement harness used by Paper 1 (shell scripts) and Paper 2 (Java threading).

What it does
------------
Runs an arbitrary command under GNU `/usr/bin/time -v`, parses the verbose
output, and returns the metrics as a structured `BenchResult` dataclass (and/or
a CSV row). Works for any executable: a bash script, a `java -jar` invocation,
a compiled binary.

Captured metrics
----------------
- wall_time_s, user_time_s, sys_time_s
- cpu_pct
- max_rss_kb (peak resident memory)
- minor_faults, major_faults
- voluntary_ctx, involuntary_ctx
- fs_inputs, fs_outputs
- exit_code

Linux-only by default (relies on GNU time + /proc semantics).
On macOS, install GNU time:    brew install gnu-time
                               export GTIME_PATH=$(which gtime)

Dependencies: stdlib only.

Quick API
---------
    from common import bench

    results = bench.run("bash scripts/original/collatz.sh 27", repetitions=10)
    bench.to_csv(results, "paper1-shell/results/collatz.csv")

CLI
---
    python -m common.bench "java -jar PC.jar --N 64 --M 4 --K 4" --reps 20 \\
        --csv paper2-concurrency/results/pc.csv
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import shlex
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable

GTIME = os.environ.get("GTIME_PATH", "/usr/bin/time")

# Regexes against the canonical labels GNU time prints with `-v`.
_TIME_PATTERNS = {
    "user_time_s":     r"User time \(seconds\):\s+([\d.]+)",
    "sys_time_s":      r"System time \(seconds\):\s+([\d.]+)",
    "cpu_pct":         r"Percent of CPU this job got:\s+(\d+)%",
    "wall_time_s":     r"Elapsed \(wall clock\) time.*?:\s*([\d:.]+)",
    "max_rss_kb":      r"Maximum resident set size \(kbytes\):\s+(\d+)",
    "minor_faults":    r"Minor \(reclaiming a frame\) page faults:\s+(\d+)",
    "major_faults":    r"Major \(requiring I/O\) page faults:\s+(\d+)",
    "voluntary_ctx":   r"Voluntary context switches:\s+(\d+)",
    "involuntary_ctx": r"Involuntary context switches:\s+(\d+)",
    "fs_inputs":       r"File system inputs:\s+(\d+)",
    "fs_outputs":      r"File system outputs:\s+(\d+)",
    "exit_code":       r"Exit status:\s+(\d+)",
}

_INT_FIELDS = {
    "max_rss_kb", "minor_faults", "major_faults",
    "voluntary_ctx", "involuntary_ctx",
    "fs_inputs", "fs_outputs", "exit_code",
}


@dataclass
class BenchResult:
    cmd: str
    rep: int
    wall_time_s: float = 0.0
    user_time_s: float = 0.0
    sys_time_s: float = 0.0
    cpu_pct: float = 0.0
    max_rss_kb: int = 0
    minor_faults: int = 0
    major_faults: int = 0
    voluntary_ctx: int = 0
    involuntary_ctx: int = 0
    fs_inputs: int = 0
    fs_outputs: int = 0
    exit_code: int = 0
    timestamp: str = field(default_factory=lambda: time.strftime("%Y-%m-%dT%H:%M:%S"))
    stdout: str = ""
    stderr: str = ""


def _parse_wall(s: str) -> float:
    """Convert GNU time's `h:mm:ss` or `m:ss.cc` into seconds."""
    parts = [float(p) for p in s.split(":")]
    if len(parts) == 3:
        h, m, sec = parts
    elif len(parts) == 2:
        h, m, sec = 0.0, parts[0], parts[1]
    else:
        h, m, sec = 0.0, 0.0, parts[0]
    return h * 3600 + m * 60 + sec


def _parse_time_output(text: str) -> dict:
    out: dict = {}
    for key, pat in _TIME_PATTERNS.items():
        m = re.search(pat, text)
        if not m:
            continue
        val = m.group(1)
        if key == "wall_time_s":
            out[key] = _parse_wall(val)
        elif key in _INT_FIELDS:
            out[key] = int(val)
        else:
            out[key] = float(val)
    return out


def _check_gnu_time() -> None:
    """Fail fast with a clear message if GTIME isn't GNU time (-v unsupported)."""
    try:
        probe = subprocess.run(
            [GTIME, "-v", "true"], capture_output=True, text=True, timeout=5
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            f"GNU time not found at {GTIME!r}. "
            "On macOS run `brew install gnu-time` and set GTIME_PATH=$(which gtime)."
        ) from e
    if "Maximum resident set size" not in probe.stderr:
        raise RuntimeError(
            f"{GTIME!r} doesn't look like GNU time (no `-v` verbose output). "
            "Set GTIME_PATH to a real GNU time binary."
        )


def run(
    cmd: str | list[str],
    *,
    repetitions: int = 1,
    cwd: str | os.PathLike | None = None,
    env: dict | None = None,
    timeout: float | None = None,
    capture_output: bool = True,
) -> list[BenchResult]:
    """Run `cmd` under GNU time and return one BenchResult per repetition."""
    _check_gnu_time()

    if isinstance(cmd, list):
        cmd_str = " ".join(shlex.quote(c) for c in cmd)
    else:
        cmd_str = cmd

    allowed = set(BenchResult.__dataclass_fields__.keys()) - {
        "cmd", "rep", "timestamp", "stdout", "stderr",
    }

    results: list[BenchResult] = []
    for r in range(repetitions):
        proc = subprocess.run(
            [GTIME, "-v", "sh", "-c", cmd_str],
            cwd=cwd, env=env, timeout=timeout,
            capture_output=capture_output, text=True,
        )
        parsed = _parse_time_output(proc.stderr)
        kwargs = {k: v for k, v in parsed.items() if k in allowed}
        results.append(
            BenchResult(
                cmd=cmd_str,
                rep=r,
                stdout=proc.stdout if capture_output else "",
                stderr=proc.stderr if capture_output else "",
                **kwargs,
            )
        )
    return results


def to_csv(
    results: Iterable[BenchResult],
    path: str | os.PathLike,
    *,
    append: bool = True,
) -> None:
    """Write/append BenchResults to a CSV file (stdout/stderr columns are dropped)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not (append and path.exists() and path.stat().st_size > 0)
    fields = [
        f for f in BenchResult.__dataclass_fields__ if f not in ("stdout", "stderr")
    ]
    mode = "a" if append else "w"
    with path.open(mode, newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if write_header:
            w.writeheader()
        for r in results:
            row = {k: asdict(r)[k] for k in fields}
            w.writerow(row)


def _main() -> None:
    p = argparse.ArgumentParser(
        description="Run a command under GNU time and emit metrics (CSV optional)."
    )
    p.add_argument("command", help="Command to run (quote it).")
    p.add_argument("--reps", type=int, default=1)
    p.add_argument("--csv", type=str, default=None, help="Append results to this CSV.")
    p.add_argument("--cwd", type=str, default=None)
    p.add_argument("--timeout", type=float, default=None)
    args = p.parse_args()

    res = run(args.command, repetitions=args.reps, cwd=args.cwd, timeout=args.timeout)
    if args.csv:
        to_csv(res, args.csv)
    for r in res:
        d = asdict(r)
        d.pop("stdout", None)
        d.pop("stderr", None)
        print(d)


if __name__ == "__main__":
    _main()
