#!/usr/bin/env bash
# rn (instrumented)
LOG_PREFIX="[rn]"

if [ $# -lt 2 ]; then
    echo "Usage: rn <old_pattern> <new_pattern> [files...]" >&2
    exit 1
fi

old_pat="$1"
new_pat="$2"
shift 2

echo "$LOG_PREFIX START  old='$old_pat'  new='$new_pat'  args=$#  pid=$$" >&2

renamed=0
skipped=0

rename_file() {
    local f="$1"
    local dir
    local base
    dir=$(dirname "$f")
    base=$(basename "$f")

    echo "$LOG_PREFIX   processing: '$f'" >&2
    local t_start=$SECONDS

    local newbase
    newbase=$(echo "$base" | sed "s/${old_pat}/${new_pat}/g")

    local t_end=$SECONDS
    echo "$LOG_PREFIX   sed took $(( t_end - t_start ))s  base='$base'  ->  '$newbase'" >&2

    if [ "$base" != "$newbase" ]; then
        local newpath
        if [ "$dir" = "." ]; then
            newpath="$newbase"
        else
            newpath="$dir/$newbase"
        fi
        mv -- "$f" "$newpath"
        echo "Renamed: $f  ->  $newpath"
        renamed=$(( renamed + 1 ))
        echo "$LOG_PREFIX   RENAMED" >&2
    else
        skipped=$(( skipped + 1 ))
        echo "$LOG_PREFIX   no match, skipped" >&2
    fi
}

if [ $# -eq 0 ]; then
    echo "$LOG_PREFIX reading filenames from stdin" >&2
    while IFS= read -r f; do
        rename_file "$f"
    done
else
    for f in "$@"; do
        if [ -e "$f" ]; then
            rename_file "$f"
        else
            echo "Warning: '$f' not found, skipping." >&2
            skipped=$(( skipped + 1 ))
        fi
    done
fi

echo "$LOG_PREFIX END  renamed=$renamed  skipped=$skipped" >&2
