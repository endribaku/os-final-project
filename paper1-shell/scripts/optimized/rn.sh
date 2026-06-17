#!/usr/bin/env bash
# rn (optimized)
# Optimization: replace `echo "$base" | sed "s/..."` (two subprocesses per file)
# with bash parameter expansion `${base//<old>/<new>}` — zero subshells,
# pure in-process string replacement.

if [ $# -lt 2 ]; then
    echo "Usage: rn <old_pattern> <new_pattern> [files...]" >&2
    exit 1
fi

old_pat="$1"
new_pat="$2"
shift 2

rename_file() {
    local f="$1"
    local dir base newbase newpath
    dir=$(dirname "$f")
    base=$(basename "$f")
    # Bash global substitution — no subprocess
    newbase="${base//${old_pat}/${new_pat}}"
    if [ "$base" != "$newbase" ]; then
        newpath="$( [ "$dir" = "." ] && echo "$newbase" || echo "$dir/$newbase" )"
        mv -- "$f" "$newpath"
        echo "Renamed: $f  ->  $newpath"
    fi
}

if [ $# -eq 0 ]; then
    while IFS= read -r f; do rename_file "$f"; done
else
    for f in "$@"; do
        [ -e "$f" ] && rename_file "$f" || echo "Warning: '$f' not found." >&2
    done
fi
