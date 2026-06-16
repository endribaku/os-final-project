#!/usr/bin/env bash
# makedict -- build a sorted, deduplicated word list from one or more text files
# Usage: makedict [file1 file2 ...] > dictionary.txt
#        cat corpus.txt | makedict
#
# Each input file is processed individually and results are merged at the end.
# Words are lowercased; punctuation and digits are stripped.

TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

process_file() {
    local f="$1"
    local out="$TMPDIR_WORK/$(basename "$f").words"

    # Extract words: replace non-alpha chars with newlines, lowercase, drop empties
    tr -cs 'A-Za-z' '\n' < "$f" \
        | tr 'A-Z' 'a-z' \
        | grep -v '^$' \
        | sort \
        > "$out"
}

if [ $# -eq 0 ]; then
    # Read from stdin
    tmpfile="$TMPDIR_WORK/stdin.tmp"
    cat > "$tmpfile"
    process_file "$tmpfile"
else
    for f in "$@"; do
        if [ -f "$f" ]; then
            process_file "$f"
        else
            echo "Warning: '$f' not found, skipping." >&2
        fi
    done
fi

# Merge all per-file word lists, sort and deduplicate
sort -m "$TMPDIR_WORK"/*.words 2>/dev/null | uniq

total=$(sort -m "$TMPDIR_WORK"/*.words 2>/dev/null | uniq | wc -l)
echo "# Total unique words: $total" >&2
