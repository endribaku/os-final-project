#!/usr/bin/env bash
# mailformat (optimized)
# Optimization: replace manual word-by-word loop with the `fold` built-in.
# `fold -s -w N` does the line-breaking in a single C-level pass — no per-word
# subshells, no bash string arithmetic per character.

WIDTH=${1:-72}

while IFS= read -r line; do
    if [ -z "$line" ]; then
        echo ""
        continue
    fi
    if [[ "$line" == ">"* ]]; then
        echo "$line"
        continue
    fi
    echo "$line" | fold -s -w "$WIDTH"
done
