#!/usr/bin/env bash
# Convenience wrapper around drivers/stress.py.
#
# Usage (from any directory):
#     ./paper2-concurrency/drivers/stress_tests.sh                 # all tests
#     ./paper2-concurrency/drivers/stress_tests.sh quick           # smoke
#     ./paper2-concurrency/drivers/stress_tests.sh dp-deadlock     # one test
#     ./paper2-concurrency/drivers/stress_tests.sh --help          # python help
#
# Pre-requisites: build the Java classes and the C binaries first.

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/../.." && pwd)"
cd "$ROOT"
export PYTHONPATH="$ROOT"

if [[ $# -eq 0 ]]; then
    exec python paper2-concurrency/drivers/stress.py --test all
fi

case "$1" in
    quick)        exec python paper2-concurrency/drivers/stress.py --quick ;;
    all)          exec python paper2-concurrency/drivers/stress.py --test all ;;
    --*|-h|help)  exec python paper2-concurrency/drivers/stress.py "$@" ;;
    *)            exec python paper2-concurrency/drivers/stress.py --test "$1" ;;
esac
