#!/usr/bin/env bash
# collatz (optimized)
# Optimizations applied:
#   1. Replace `$(( current % 2 ))` subshell test with arithmetic `(( ))` — no
#      subshell, result goes directly into branch condition.
#   2. Accumulate sequence in a bash array and print once with a single echo
#      instead of echo -n per step (reduces I/O syscalls from O(steps) to O(1)).
#   3. Use (( )) throughout — avoids quoting overhead of [ ] with integers.

N="${1:-27}"

if ! [[ "$N" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: collatz <positive integer>" >&2; exit 1
fi

current=$N
steps=0
max_val=$N
seq=("$N")

while (( current != 1 )); do
    if (( current % 2 == 0 )); then
        (( current /= 2 ))
    else
        (( current = current * 3 + 1 ))
    fi
    seq+=("$current")
    (( steps++ ))
    (( current > max_val )) && max_val=$current
done

echo "Sequence: ${seq[*]}"
echo "Start:     $N"
echo "Steps:     $steps"
echo "Max value: $max_val"
