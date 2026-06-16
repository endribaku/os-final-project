#!/usr/bin/env bash
# makedict (optimized)
# Optimization: eliminate per-file temp files and the final sort-merge step.
# All input files are fed into a single pipeline: cat → tr → tr → grep → sort → uniq.
# One pipeline = one fork per stage, constant regardless of file count.
# The original creates N temp files + N sort processes + 1 sort-merge.

if [ $# -eq 0 ]; then
    tr -cs 'A-Za-z' '\n' \
        | tr 'A-Z' 'a-z' \
        | grep -v '^$' \
        | sort -u
else
    # Validate files first, warn on missing
    valid_files=()
    for f in "$@"; do
        if [ -f "$f" ]; then
            valid_files+=("$f")
        else
            echo "Warning: '$f' not found, skipping." >&2
        fi
    done

    if [ ${#valid_files[@]} -eq 0 ]; then
        echo "Error: no valid input files." >&2; exit 1
    fi

    cat -- "${valid_files[@]}" \
        | tr -cs 'A-Za-z' '\n' \
        | tr 'A-Z' 'a-z' \
        | grep -v '^$' \
        | sort -u
fi
