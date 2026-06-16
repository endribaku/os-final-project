#!/usr/bin/env bash
# tree (optimized)
# Optimization: the original calls `find "$dir" -maxdepth 1` once per directory,
# meaning O(total_dirs) find processes. Replace with a single top-level
# `find "$ROOT"` that lists everything, then reconstruct the tree in-process
# by sorting on path depth and using an associative array of prefix strings.
# Result: 1 find call total instead of N.

ROOT="${1:-.}"
MAX_DEPTH="${2:-9999}"

if [ ! -d "$ROOT" ]; then
    echo "Error: '$ROOT' is not a directory." >&2; exit 1
fi

total_dirs=0
total_files=0

# Collect all paths with depth info in one find call
declare -a all_paths
while IFS= read -r -d '' p; do
    all_paths+=("$p")
done < <(find "$ROOT" -mindepth 1 -print0 2>/dev/null | sort -z)

# Build parent→children map
declare -A children
for p in "${all_paths[@]}"; do
    parent=$(dirname "$p")
    children["$parent"]+="$p"$'\n'
done

# Track connector prefix per directory
declare -A prefix_map
prefix_map["$ROOT"]=""

print_node() {
    local dir="$1"
    local pre="${prefix_map[$dir]}"
    local -a kids
    mapfile -t kids < <(printf '%s' "${children[$dir]:-}" | sort)
    local n=${#kids[@]}
    local i=0
    for kid in "${kids[@]}"; do
        [ -z "$kid" ] && continue
        local name
        name=$(basename "$kid")
        (( i++ ))
        if (( i == n )); then
            echo "${pre}└── $name"
            prefix_map["$kid"]="${pre}    "
        else
            echo "${pre}├── $name"
            prefix_map["$kid"]="${pre}│   "
        fi
        if [ -d "$kid" ]; then
            (( total_dirs++ ))
            print_node "$kid"
        else
            (( total_files++ ))
        fi
    done
}

echo "$ROOT"
print_node "$ROOT"
echo ""
echo "$total_dirs director$([ "$total_dirs" -eq 1 ] && echo 'y' || echo 'ies'), $total_files file$([ "$total_files" -eq 1 ] && echo '' || echo 's')"
