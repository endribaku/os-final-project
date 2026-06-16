#!/usr/bin/env bash
# blank-rename (optimized)
# Optimization: replace `echo "$base" | grep -q '[[:space:]]'` and
# `echo "$base" | tr '[:space:]' '_'` (two subprocesses per file) with
# bash `[[ $base == *[[:space:]]* ]]` and `${base//[[:space:]]/_}` —
# zero subshells for the hot path.

DIR="${1:-.}"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' is not a directory." >&2
    exit 1
fi

count=0
skipped=0

for filepath in "$DIR"/*; do
    [ -e "$filepath" ] || continue
    base=$(basename "$filepath")

    if [[ "$base" == *[[:space:]]* ]]; then
        newbase="${base//[[:space:]]/_}"
        newpath="$DIR/$newbase"
        if [ -e "$newpath" ]; then
            echo "Skip (target exists): '$base'  ->  '$newbase'" >&2
            skipped=$(( skipped + 1 ))
        else
            mv -- "$filepath" "$newpath"
            echo "Renamed: '$base'  ->  '$newbase'"
            count=$(( count + 1 ))
        fi
    fi
done

echo "Done. $count file(s) renamed, $skipped skipped."
