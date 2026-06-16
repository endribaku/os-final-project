#!/usr/bin/env bash
# blank-rename (instrumented)
LOG_PREFIX="[blank-rename]"

DIR="${1:-.}"

if [ ! -d "$DIR" ]; then
    echo "Error: '$DIR' is not a directory." >&2
    exit 1
fi

echo "$LOG_PREFIX START  dir='$DIR'  pid=$$" >&2

total_scanned=0
count=0
skipped=0

for filepath in "$DIR"/*; do
    [ -e "$filepath" ] || continue

    total_scanned=$(( total_scanned + 1 ))
    base=$(basename "$filepath")
    echo "$LOG_PREFIX   scanning: '$base'" >&2

    if echo "$base" | grep -q '[[:space:]]'; then
        newbase=$(echo "$base" | tr '[:space:]' '_')
        newpath="$DIR/$newbase"
        echo "$LOG_PREFIX   has spaces -> '$newbase'" >&2

        if [ -e "$newpath" ]; then
            echo "Skip (target exists): '$base'  ->  '$newbase'" >&2
            skipped=$(( skipped + 1 ))
            echo "$LOG_PREFIX   SKIPPED (collision)" >&2
        else
            mv -- "$filepath" "$newpath"
            echo "Renamed: '$base'  ->  '$newbase'"
            count=$(( count + 1 ))
            echo "$LOG_PREFIX   RENAMED" >&2
        fi
    else
        echo "$LOG_PREFIX   no spaces, skip" >&2
    fi
done

echo "$LOG_PREFIX END  scanned=$total_scanned  renamed=$count  skipped=$skipped" >&2
echo "Done. $count file(s) renamed, $skipped skipped."
