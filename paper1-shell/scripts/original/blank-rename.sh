#!/usr/bin/env bash
# blank-rename -- replace whitespace in filenames with underscores
# Usage: blank-rename [directory]
# Processes all files one level deep in the given directory (default: current).

DIR="${1:-.}"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' is not a directory." >&2
    exit 1
fi

count=0
skipped=0

for filepath in "$DIR"/*; do
    [ -e "$filepath" ] || continue          # skip if glob matched nothing

    base=$(basename "$filepath")

    # Check whether the name contains any whitespace
    if echo "$base" | grep -q '[[:space:]]'; then
        newbase=$(echo "$base" | tr '[:space:]' '_')
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
