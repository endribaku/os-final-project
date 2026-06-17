#!/usr/bin/env bash
# tree (instrumented) -- logs each find call and recursion depth
LOG_PREFIX="[tree]"

ROOT="${1:-.}"
MAX_DEPTH="${2:-9999}"

if [ ! -d "$ROOT" ]; then
    echo "Error: '$ROOT' is not a directory." >&2
    exit 1
fi

echo "$LOG_PREFIX START  root='$ROOT'  max_depth=$MAX_DEPTH  pid=$$" >&2

total_dirs=0
total_files=0
find_calls=0

print_tree() {
    local dir="$1"
    local prefix="$2"
    local depth="$3"

    [ "$depth" -gt "$MAX_DEPTH" ] && return

    find_calls=$(( find_calls + 1 ))
    echo "$LOG_PREFIX   find call #$find_calls: dir='$dir'  depth=$depth" >&2

    local entries=()
    while IFS= read -r -d '' entry; do
        entries+=("$entry")
    done < <(find "$dir" -maxdepth 1 -mindepth 1 -print0 2>/dev/null | sort -z)

    local total=${#entries[@]}
    echo "$LOG_PREFIX   '$dir': $total entries at depth=$depth" >&2
    local idx=0

    for entry in "${entries[@]}"; do
        idx=$(( idx + 1 ))
        local name
        name=$(basename "$entry")

        if [ "$idx" -eq "$total" ]; then
            echo "${prefix}└── ${name}"
            local child_prefix="${prefix}    "
        else
            echo "${prefix}├── ${name}"
            local child_prefix="${prefix}│   "
        fi

        if [ -d "$entry" ]; then
            total_dirs=$(( total_dirs + 1 ))
            echo "$LOG_PREFIX   entering dir '$name' at depth=$(( depth+1 ))" >&2
            print_tree "$entry" "$child_prefix" $(( depth + 1 ))
        else
            total_files=$(( total_files + 1 ))
            echo "$LOG_PREFIX   file: '$name'" >&2
        fi
    done
}

echo "$ROOT"
print_tree "$ROOT" "" 1
echo ""
echo "$total_dirs director$([ "$total_dirs" -eq 1 ] && echo 'y' || echo 'ies'), $total_files file$([ "$total_files" -eq 1 ] && echo '' || echo 's')"
echo "$LOG_PREFIX END  dirs=$total_dirs  files=$total_files  find_calls=$find_calls" >&2
