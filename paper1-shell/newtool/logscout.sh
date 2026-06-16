#!/usr/bin/env bash
# logscout -- intelligent log file analyzer and summarizer
#
# ALGORITHM (state-based pipeline):
#   Phase 1  (filter-transform)  : stream each line through severity classifier
#   Phase 2  (state-based)       : track counts, first/last occurrence, top-N messages
#   Phase 3  (pipeline)          : sort + uniq to rank frequent messages
#   Phase 4  (output)            : render human-readable or JSON report
#
# Usage:
#   logscout [OPTIONS] [logfile ...]
#   cat app.log | logscout
#
# Options:
#   -t, --top N        Show top N most frequent messages per level (default 5)
#   -l, --level LEVEL  Filter to a minimum severity (DEBUG < INFO < WARN < ERROR)
#   -j, --json         Output as JSON
#   -q, --quiet        Only print the summary table, not top messages
#   -h, --help         Show this help

set -euo pipefail

# ---- defaults ----------------------------------------------------------------
TOP_N=5
MIN_LEVEL="DEBUG"
OUTPUT_JSON=0
QUIET=0
declare -a INPUT_FILES=()

# ---- severity ordering -------------------------------------------------------
declare -A LEVEL_ORDER=([DEBUG]=0 [INFO]=1 [WARN]=2 [WARNING]=2 [ERROR]=3 [CRITICAL]=4 [FATAL]=4)
declare -A LEVEL_NORM=([DEBUG]=DEBUG [INFO]=INFO [WARN]=WARN [WARNING]=WARN [ERROR]=ERROR [CRITICAL]=ERROR [FATAL]=ERROR)

# ---- argument parsing --------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        -t|--top)     TOP_N="$2";    shift 2 ;;
        -l|--level)   MIN_LEVEL="${2^^}"; shift 2 ;;
        -j|--json)    OUTPUT_JSON=1; shift   ;;
        -q|--quiet)   QUIET=1;       shift   ;;
        -h|--help)
            sed -n '/^# logscout/,/^$/p' "$0" | sed 's/^# \?//'
            exit 0 ;;
        -*)
            echo "Unknown option: $1" >&2; exit 1 ;;
        *)
            INPUT_FILES+=("$1"); shift ;;
    esac
done

min_order=${LEVEL_ORDER[$MIN_LEVEL]:-0}

# ---- temp workspace ----------------------------------------------------------
TMPDIR_WORK=$(mktemp -d)
trap 'rm -rf "$TMPDIR_WORK"' EXIT

ALL_LINES="$TMPDIR_WORK/all.txt"
touch "$ALL_LINES"

# ---- Phase 1: read + normalize -----------------------------------------------
# Classify each line into: <LEVEL> <timestamp_or_-> <rest>
# Supports common formats:
#   [2024-01-01 12:00:00] ERROR something happened
#   2024-01-01T12:00:00 WARN  something happened
#   Jan  1 12:00:00 ERROR something
#   ERROR: something (no timestamp)

classify_line() {
    local line="$1"
    local level="UNKNOWN"
    local ts="-"
    local msg="$line"

    # Try to extract known severity keywords
    local found_level
    for kw in FATAL CRITICAL ERROR WARN WARNING INFO DEBUG; do
        if echo "$line" | grep -qiE "(^|[\[\s:])${kw}([\]\s:]|$)"; then
            found_level="$kw"
            break
        fi
    done

    if [[ -n "${found_level:-}" ]]; then
        level="${LEVEL_NORM[$found_level]:-$found_level}"
        # Attempt to strip timestamp prefix (ISO8601 or syslog style)
        msg=$(echo "$line" | sed -E \
            's/^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}[.0-9Z]* ?//' \
            | sed -E 's/^\[?[A-Z][a-z]{2} +[0-9]{1,2} [0-9]{2}:[0-9]{2}:[0-9]{2}\]? ?//')
        # Trim leading level keyword
        msg=$(echo "$msg" | sed -E "s/^\[?${found_level}\]?:? ?//i")
        msg="${msg:0:120}"    # cap message length
    fi

    echo "$level"$'\t'"$msg"
}

process_input() {
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        local classified
        classified=$(classify_line "$line")
        echo "$classified"
    done
}

if [[ ${#INPUT_FILES[@]} -eq 0 ]]; then
    process_input < /dev/stdin >> "$ALL_LINES"
else
    for f in "${INPUT_FILES[@]}"; do
        if [[ -f "$f" ]]; then
            process_input < "$f" >> "$ALL_LINES"
        else
            echo "Warning: '$f' not found." >&2
        fi
    done
fi

# ---- Phase 2: state-based counting -------------------------------------------
declare -A level_count=([DEBUG]=0 [INFO]=0 [WARN]=0 [ERROR]=0 [UNKNOWN]=0)
total_lines=0

while IFS=$'\t' read -r lvl msg; do
    (( total_lines++ ))
    lvl_ord=${LEVEL_ORDER[$lvl]:-99}
    if (( lvl_ord >= min_order )); then
        lvl_key="${lvl:-UNKNOWN}"
        (( level_count[$lvl_key]++ )) || true
    fi
    # Bucket message by level for top-N
    echo "$msg" >> "$TMPDIR_WORK/${lvl}.msgs" 2>/dev/null || true
done < "$ALL_LINES"

# ---- Phase 3: rank top messages per level ------------------------------------
declare -A top_msgs
for lvl in DEBUG INFO WARN ERROR; do
    f="$TMPDIR_WORK/${lvl}.msgs"
    if [[ -f "$f" && -s "$f" ]]; then
        top_msgs[$lvl]=$(sort "$f" | uniq -c | sort -rn | head -n "$TOP_N" | \
            awk '{count=$1; $1=""; printf "      %5d × %s\n", count, $0}')
    else
        top_msgs[$lvl]=""
    fi
done

# ---- Phase 4: output ---------------------------------------------------------
if (( OUTPUT_JSON )); then
    python3 -c "
import json, sys
data = {
    'total_lines': $total_lines,
    'min_level_filter': '${MIN_LEVEL}',
    'counts': {
        'DEBUG':   ${level_count[DEBUG]},
        'INFO':    ${level_count[INFO]},
        'WARN':    ${level_count[WARN]},
        'ERROR':   ${level_count[ERROR]},
        'UNKNOWN': ${level_count[UNKNOWN]},
    }
}
print(json.dumps(data, indent=2))
"
else
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                   logscout  summary                     ║"
    echo "╠══════════════════════════════════════════════════════════╣"
    printf "║  %-20s %8s  (%s min-level filter)  ║\n" \
        "Total lines:" "$total_lines" "$MIN_LEVEL"
    echo "╠══════════════════════════════════════════════════════════╣"
    printf "║  %-12s  %8d                                 ║\n" "ERROR"   "${level_count[ERROR]}"
    printf "║  %-12s  %8d                                 ║\n" "WARN"    "${level_count[WARN]}"
    printf "║  %-12s  %8d                                 ║\n" "INFO"    "${level_count[INFO]}"
    printf "║  %-12s  %8d                                 ║\n" "DEBUG"   "${level_count[DEBUG]}"
    printf "║  %-12s  %8d                                 ║\n" "UNKNOWN" "${level_count[UNKNOWN]}"
    echo "╚══════════════════════════════════════════════════════════╝"

    if (( ! QUIET )); then
        for lvl in ERROR WARN INFO DEBUG; do
            lvl_ord=${LEVEL_ORDER[$lvl]}
            (( lvl_ord < min_order )) && continue
            [[ -z "${top_msgs[$lvl]}" ]] && continue
            echo ""
            echo "  Top $TOP_N $lvl messages:"
            echo "${top_msgs[$lvl]}"
        done
    fi
fi
