#!/usr/bin/env bash
# collatz (instrumented)
LOG_PREFIX="[collatz]"

N="${1:-27}"

if ! [[ "$N" =~ ^[1-9][0-9]*$ ]]; then
    echo "Usage: collatz <positive integer>" >&2
    exit 1
fi

echo "$LOG_PREFIX START  n=$N  pid=$$" >&2

current="$N"
steps=0
max_val="$N"
even_steps=0
odd_steps=0

echo -n "Sequence: $current"

while [ "$current" -ne 1 ]; do
    if [ $(( current % 2 )) -eq 0 ]; then
        current=$(( current / 2 ))
        even_steps=$(( even_steps + 1 ))
        echo "$LOG_PREFIX   step $steps: even -> $current" >&2
    else
        current=$(( current * 3 + 1 ))
        odd_steps=$(( odd_steps + 1 ))
        echo "$LOG_PREFIX   step $steps: odd  -> $current" >&2
    fi

    echo -n " $current"
    steps=$(( steps + 1 ))

    if [ "$current" -gt "$max_val" ]; then
        max_val="$current"
        echo "$LOG_PREFIX   new max: $max_val at step $steps" >&2
    fi
done

echo ""
echo "Start:      $N"
echo "Steps:      $steps"
echo "Max value:  $max_val"
echo "$LOG_PREFIX END  steps=$steps  even=$even_steps  odd=$odd_steps  max=$max_val" >&2
