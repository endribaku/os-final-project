#!/usr/bin/env bash
# Fast end-to-end check of the Paper 2 pipeline:
#   - sweep_pc.py --quick   (single-config PC run per impl)
#   - sweep_dp.py --quick   (single-config DP run per impl)
#   - plot_pc.py / plot_dp.py
# Produces:
#   paper2-concurrency/results/pc_sweep.csv
#   paper2-concurrency/results/dp_sweep.csv
#   paper2-concurrency/figures/{pc,dp}/*.png
#
# Run AFTER ./paper2-concurrency/build.sh.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$ROOT"

# auto-activate the venv if one is sitting where ENVIRONMENT.md expects.
if [[ -z "${VIRTUAL_ENV:-}" && -f "$HOME/.venvs/osproj/bin/activate" ]]; then
    echo "(activating venv at ~/.venvs/osproj)"
    # shellcheck disable=SC1091
    source "$HOME/.venvs/osproj/bin/activate"
fi

export PYTHONPATH="$ROOT"

echo ">>> sweep_pc --quick"
python paper2-concurrency/drivers/sweep_pc.py --quick

echo
echo ">>> sweep_dp --quick"
python paper2-concurrency/drivers/sweep_dp.py --quick

echo
echo ">>> plot_pc"
python paper2-concurrency/drivers/plot_pc.py

echo
echo ">>> plot_dp"
python paper2-concurrency/drivers/plot_dp.py

echo
echo "[smoke] CSVs:"
ls -1 "$HERE"/results/*.csv 2>/dev/null || echo "  (none)"
echo "[smoke] figures:"
find "$HERE"/figures -name "*.png" 2>/dev/null || echo "  (none)"
