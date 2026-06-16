#!/usr/bin/env bash
# makedict (instrumented)
LOG_PREFIX="[makedict]"

TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

echo "$LOG_PREFIX START  args=$#  pid=$$" >&2

process_file() {
    local f="$1"
    local out="$TMPDIR_WORK/$(basename "$f").words"
    local size
    size=$(wc -c < "$f")
    echo "$LOG_PREFIX   processing: '$f'  size=${size}B" >&2

    local t0=$SECONDS
    tr -cs 'A-Za-z' '\n' < "$f" \
        | tr 'A-Z' 'a-z' \
        | grep -v '^$' \
        | sort \
        > "$out"
    local t1=$SECONDS

    local wcount
    wcount=$(wc -l < "$out")
    echo "$LOG_PREFIX   '$f' -> $wcount sorted tokens  (${t1-t0}s)" >&2
}

if [ $# -eq 0 ]; then
    echo "$LOG_PREFIX   reading from stdin" >&2
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

echo "$LOG_PREFIX   merging per-file word lists..." >&2
t_merge0=$SECONDS
result=$(sort -m "$TMPDIR_WORK"/*.words 2>/dev/null | uniq)
t_merge1=$SECONDS

echo "$result"

total=$(echo "$result" | wc -l)
echo "$LOG_PREFIX END  unique_words=$total  merge_time=$((t_merge1-t_merge0))s" >&2
echo "# Total unique words: $total" >&2
