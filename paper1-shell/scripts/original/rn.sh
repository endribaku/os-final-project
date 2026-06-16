#!/usr/bin/env bash
# rn -- rename files by substituting a pattern in their names
# Usage: rn <old_pattern> <new_pattern> [files...]
#   or:  ls | rn <old_pattern> <new_pattern>
# Example: rn '.txt' '.bak' *.txt

if [ $# -lt 2 ]; then
    echo "Usage: rn <old_pattern> <new_pattern> [files...]" >&2
    exit 1
fi

old_pat="$1"
new_pat="$2"
shift 2

rename_file() {
    local f="$1"
    local dir
    local base
    dir=$(dirname "$f")
    base=$(basename "$f")
    local newbase
    newbase=$(echo "$base" | sed "s/${old_pat}/${new_pat}/g")
    if [ "$base" != "$newbase" ]; then
        local newpath
        if [ "$dir" = "." ]; then
            newpath="$newbase"
        else
            newpath="$dir/$newbase"
        fi
        mv -- "$f" "$newpath"
        echo "Renamed: $f  ->  $newpath"
    fi
}

if [ $# -eq 0 ]; then
    while IFS= read -r f; do
        rename_file "$f"
    done
else
    for f in "$@"; do
        if [ -e "$f" ]; then
            rename_file "$f"
        else
            echo "Warning: '$f' not found, skipping." >&2
        fi
    done
fi
