#!/usr/bin/env bash
# collatz -- compute the Collatz (3n+1) sequence for a starting number
# Usage: collatz <n>
# Prints each term and the total step count.

N="${1:-27}"

if ! [[ "$N" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: collatz <positive integer>" >&2
    exit 1
fi

current="$N"
steps=0
max_val="$N"

echo -n "Sequence: $current"

while [ "$current" -ne 1 ]; do
    if [ $(( current % 2 )) -eq 0 ]; then
        current=$(( current / 2 ))
    else
        current=$(( current * 3 + 1 ))
    fi

    echo -n " $current"
    steps=$(( steps + 1 ))

    if [ "$current" -gt "$max_val" ]; then
        max_val="$current"
    fi
done

echo ""
echo "Start:     $N"
echo "Steps:     $steps"
echo "Max value: $max_val"
