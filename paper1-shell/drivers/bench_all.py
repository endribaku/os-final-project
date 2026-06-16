#!/usr/bin/env python3
"""
drivers/bench_all.py
--------------------
Benchmark driver for Paper 1 shell scripts.

For each of the 10 scripts it builds representative input/argument sets from
config/experiments.yaml, runs both the original and optimized variants under
GNU time (via common.bench), and writes per-script CSVs to results/.

Also benchmarks the logscout new tool.

Usage (from repo root):
    python3 paper1-shell/drivers/bench_all.py [--reps N] [--scripts a b ...]

Outputs:
    paper1-shell/results/<script>_original.csv
    paper1-shell/results/<script>_optimized.csv
    paper1-shell/results/logscout_newtool.csv
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

# Make common importable from any CWD
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

import yaml
from common import bench

# ---------------------------------------------------------------------------
PAPER1 = REPO_ROOT / "paper1-shell"
ORIG    = PAPER1 / "scripts" / "original"
OPT     = PAPER1 / "scripts" / "optimized"
NEWTOOL = PAPER1 / "newtool"
RESULTS = PAPER1 / "results"
RESULTS.mkdir(parents=True, exist_ok=True)

CFG = yaml.safe_load((REPO_ROOT / "config" / "experiments.yaml").read_text())
P1  = CFG["paper1"]
REPS_DEFAULT = P1.get("repetitions", 20)
INPUT_SIZES  = P1["input_sizes"]


# ---------------------------------------------------------------------------
# Input-set builders — return a list of (label, arg_string) tuples
# ---------------------------------------------------------------------------

def _tmpfile(content: str, suffix: str = ".txt") -> str:
    """Write content to a temp file, return its path (caller must delete)."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(content)
    f.close()
    return f.name


def inputs_mailformat() -> list[tuple[str, str]]:
    cases = []
    for width in P1["mailformat_line_widths"]:
        # 500-word paragraph as stdin
        words = " ".join(["word"] * 500)
        tf = _tmpfile(words)
        cases.append((f"width{width}", f"bash {{script}} {width} < {tf}"))
    return cases


def inputs_rn() -> list[tuple[str, str]]:
    """Create temp files with .tmp extension, rename them."""
    cases = []
    for size in ["small", "medium", "large"]:
        n = INPUT_SIZES[size]
        tmpdir = tempfile.mkdtemp()
        for i in range(min(n, 200)):          # cap at 200 files
            Path(tmpdir, f"file_{i:05d}.tmp").touch()
        cases.append((size, f"bash {{script}} '\\.tmp' '.bak' {tmpdir}/file_*.tmp"))
    return cases


def inputs_blank_rename() -> list[tuple[str, str]]:
    cases = []
    for size in ["small", "medium"]:
        n = min(INPUT_SIZES[size], 200)
        tmpdir = tempfile.mkdtemp()
        for i in range(n):
            Path(tmpdir, f"file {i:04d}.txt").touch()
        cases.append((size, f"bash {{script}} {tmpdir}"))
    return cases


def inputs_encryptedpw() -> list[tuple[str, str]]:
    cases = []
    for n in [10, 100, 500]:
        text = "HelloWorld" * (n // 10)
        cases.append((f"len{n}", f"bash {{script}} encrypt '{text}'"))
    return cases


def inputs_collatz() -> list[tuple[str, str]]:
    return [(f"n{n}", f"bash {{script}} {n}") for n in P1["collatz_seeds"]]


def inputs_days_between() -> list[tuple[str, str]]:
    return [
        (f"pair{i+1}", f"bash {{script}} '{d1}' '{d2}'")
        for i, (d1, d2) in enumerate(P1["days_between_pairs"])
    ]


def inputs_game_of_life() -> list[tuple[str, str]]:
    cases = []
    for gens in P1["game_of_life_generations"]:
        cases.append((f"gens{gens}_10x20",  f"bash {{script}} {gens} 10 20"))
        cases.append((f"gens{gens}_20x40",  f"bash {{script}} {gens} 20 40"))
    return cases


def inputs_primes() -> list[tuple[str, str]]:
    return [
        ("n100",    "bash {script} 100"),
        ("n500",    "bash {script} 500"),
        ("n1000",   "bash {script} 1000"),
        ("n5000",   "bash {script} 5000"),
    ]


def inputs_makedict() -> list[tuple[str, str]]:
    cases = []
    for size in ["small", "medium", "large"]:
        n_words = INPUT_SIZES[size]
        words = "\n".join(["alpha", "beta", "gamma", "delta", "epsilon"] * (n_words // 5))
        tf = _tmpfile(words)
        cases.append((size, f"bash {{script}} {tf}"))
    return cases


def inputs_tree() -> list[tuple[str, str]]:
    cases = []
    for depth, width in [(2, 10), (3, 8), (4, 5)]:
        tmpdir = tempfile.mkdtemp()
        # build a directory tree
        def make_tree(root: Path, d: int, w: int):
            for i in range(w):
                (root / f"file_{i}.txt").touch()
                if d > 1:
                    sub = root / f"dir_{i}"
                    sub.mkdir()
                    make_tree(sub, d - 1, w)
        make_tree(Path(tmpdir), depth, width)
        cases.append((f"d{depth}w{width}", f"bash {{script}} {tmpdir}"))
    return cases


INPUT_BUILDERS = {
    "mailformat":    inputs_mailformat,
    "rn":            inputs_rn,
    "blank-rename":  inputs_blank_rename,
    "encryptedpw":   inputs_encryptedpw,
    "collatz":       inputs_collatz,
    "days-between":  inputs_days_between,
    "game_of_life":  inputs_game_of_life,
    "primes":        inputs_primes,
    "makedict":      inputs_makedict,
    "tree":          inputs_tree,
}


# ---------------------------------------------------------------------------
def bench_script(name: str, variant: str, script_path: Path, reps: int) -> None:
    csv_path = RESULTS / f"{name}_{variant}.csv"
    print(f"\n{'='*60}")
    print(f"  {name}  [{variant}]  →  {csv_path.name}")
    print(f"{'='*60}")

    if not script_path.exists():
        print(f"  SKIP — {script_path} not found")
        return

    cases = INPUT_BUILDERS[name]()
    for label, cmd_template in cases:
        cmd = cmd_template.format(script=str(script_path))
        print(f"  input={label!r}  cmd={cmd[:80]!r}")
        results = bench.run(cmd, repetitions=reps)
        for r in results:
            r.cmd = f"{name}:{variant}:{label}"
        bench.to_csv(results, csv_path, append=True)
        wall_times = [r.wall_time_s for r in results]
        mean_w = sum(wall_times) / len(wall_times)
        print(f"    mean wall = {mean_w:.3f}s  ({reps} reps)")


def bench_logscout(reps: int) -> None:
    script = NEWTOOL / "logscout.sh"
    gen    = NEWTOOL / "gen_test_log.sh"
    csv_path = RESULTS / "logscout_newtool.csv"
    print(f"\n{'='*60}\n  logscout  [newtool]\n{'='*60}")

    if not script.exists():
        print("  SKIP — logscout.sh not found"); return

    for n_lines in [1000, 10000, 100000]:
        tf = _tmpfile("", suffix=".log")
        subprocess.run(["bash", str(gen), str(n_lines), tf], check=True,
                       capture_output=True)
        cmd = f"bash {script} {tf}"
        print(f"  lines={n_lines}")
        results = bench.run(cmd, repetitions=reps)
        for r in results:
            r.cmd = f"logscout:lines{n_lines}"
        bench.to_csv(results, csv_path, append=True)
        mean_w = sum(r.wall_time_s for r in results) / len(results)
        print(f"    mean wall = {mean_w:.3f}s")
        os.unlink(tf)


# ---------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description="Benchmark all Paper 1 shell scripts")
    ap.add_argument("--reps", type=int, default=REPS_DEFAULT)
    ap.add_argument("--scripts", nargs="*", default=list(INPUT_BUILDERS.keys()),
                    help="Subset of scripts to benchmark")
    ap.add_argument("--variant", choices=["original", "optimized", "both"],
                    default="both")
    args = ap.parse_args()

    for name in args.scripts:
        if name not in INPUT_BUILDERS:
            print(f"Unknown script: {name}", file=sys.stderr); continue
        script_name = f"{name}.sh"
        if args.variant in ("original", "both"):
            bench_script(name, "original",  ORIG / script_name,  args.reps)
        if args.variant in ("optimized", "both"):
            bench_script(name, "optimized", OPT  / script_name,  args.reps)

    bench_logscout(args.reps)
    print("\nAll benchmarks done.")


if __name__ == "__main__":
    main()
