#!/usr/bin/env bash
# install_logscout_v2.sh
# Run this ON YOUR LINUX VM from the repo root (~/os-final-project)
# to create paper1-shell/newtool/logscout_v2.sh with the optimized
# implementation. Usage: bash install_logscout_v2.sh

set -e

if [ ! -d "paper1-shell/newtool" ]; then
    echo "ERROR: paper1-shell/newtool/ not found." >&2
    echo "Run this script from the repo root (~/os-final-project)." >&2
    exit 1
fi

cat > paper1-shell/newtool/logscout_v2.sh << 'LOGSCOUT_V2_EOF'
#!/usr/bin/env bash
# logscout_v2 -- intelligent log file analyzer and summarizer (OPTIMIZED)
#
# OPTIMIZATION NOTE (vs. original logscout.sh):
#   The original's classify_line() forked up to ~11 subshells PER LINE:
#     - one $(...) to capture the function's own return value
#     - up to 7 `echo ... | grep -qiE ...` pipelines (one per severity keyword,
#       in the worst case where no early keyword matches)
#     - 2 chained `echo ... | sed -E ... | sed -E ...` pipelines to strip
#       timestamps
#     - 1 more `echo ... | sed -E ...` to strip the leading level keyword
#   At N lines, worst case that's O(11*N) forked processes, and fork/exec is
#   expensive relative to in-process work. This dominates wall-clock and
#   sys-time at scale (confirmed empirically: 1k lines ~47s, 10k lines ~405s
#   on the reference VM -- ~8.6x time for 10x data, i.e. still roughly linear
#   in lines, but with a brutal per-line constant from forking).
#
#   FIX: classify_line() below uses Bash's native regex engine ([[ =~ ]]) and
#   parameter expansion exclusively. Zero subshells are forked per line in the
#   hot path. The function communicates results via global variables
#   (REPLY_LEVEL, REPLY_MSG) instead of via command substitution, which avoids
#   the implicit subshell that $(...) would otherwise create.
#
# ALGORITHM (state-based pipeline) -- same structure as v1:
#   Phase 1  (filter-transform)  : stream each line through severity classifier
#   Phase 2  (state-based)       : track counts, first/last occurrence, top-N messages
#   Phase 3  (pipeline)          : sort + uniq to rank frequent messages
#   Phase 4  (output)            : render human-readable or JSON report
#
# Usage:
#   logscout_v2 [OPTIONS] [logfile ...]
#   cat app.log | logscout_v2
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
            sed -n '/^# logscout_v2/,/^$/p' "$0" | sed 's/^# \?//'
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

# ---- precompiled regex patterns (built once, not per line) -------------------
# Word-boundary-ish: keyword must be preceded by start/space/[/: and followed
# by end/space/]/: -- mirrors the original's grep -E "(^|[\[\s:])KW([\]\s:]|$)"
RE_FATAL_CRIT='(^|[[:space:]]|\[|:)(FATAL|CRITICAL)([[:space:]]|\]|:|$)'
RE_ERROR='(^|[[:space:]]|\[|:)ERROR([[:space:]]|\]|:|$)'
RE_WARN='(^|[[:space:]]|\[|:)(WARN|WARNING)([[:space:]]|\]|:|$)'
RE_INFO='(^|[[:space:]]|\[|:)INFO([[:space:]]|\]|:|$)'
RE_DEBUG='(^|[[:space:]]|\[|:)DEBUG([[:space:]]|\]|:|$)'

# ISO8601 timestamp prefix, e.g. "2024-01-01T12:00:00.123Z " or "2024-01-01 12:00:00 "
RE_TS_ISO='^[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]+)?Z?[[:space:]]?(.*)$'
# syslog-style timestamp, e.g. "[Jan  1 12:00:00] " or "Jan 1 12:00:00 "
RE_TS_SYSLOG='^\[?[A-Z][a-z]{2}[[:space:]]+[0-9]{1,2}[[:space:]][0-9]{2}:[0-9]{2}:[0-9]{2}\]?[[:space:]]?(.*)$'

# Globals used to return values from classify_line without forking a subshell.
REPLY_LEVEL=""
REPLY_MSG=""

classify_line() {
    local line="$1"
    local level="UNKNOWN"
    local found_kw=""
    local msg="$line"

    # Determine severity using native regex matching -- no forks.
    if [[ "$line" =~ $RE_FATAL_CRIT ]]; then
        level="ERROR"; found_kw=1
    elif [[ "$line" =~ $RE_ERROR ]]; then
        level="ERROR"; found_kw=1
    elif [[ "$line" =~ $RE_WARN ]]; then
        level="WARN"; found_kw=1
    elif [[ "$line" =~ $RE_INFO ]]; then
        level="INFO"; found_kw=1
    elif [[ "$line" =~ $RE_DEBUG ]]; then
        level="DEBUG"; found_kw=1
    fi

    if [[ -n "$found_kw" ]]; then
        # Strip ISO8601 timestamp prefix, if present.
        if [[ "$msg" =~ $RE_TS_ISO ]]; then
            msg="${BASH_REMATCH[2]}"
        fi
        # Strip syslog-style timestamp prefix, if present.
        if [[ "$msg" =~ $RE_TS_SYSLOG ]]; then
            msg="${BASH_REMATCH[1]}"
        fi
        # Strip a leading level keyword like "ERROR:" or "[ERROR]" -- case
        # insensitive match via the lowercase/uppercase fold built into bash.
        local msg_lc="${msg,,}"
        for kw in fatal critical error warning warn info debug; do
            if [[ "$msg_lc" == "$kw"* ]]; then
                msg="${msg:${#kw}}"
                msg="${msg#:}"
                msg="${msg# }"
                break
            elif [[ "$msg_lc" == "["$kw* ]]; then
                msg="${msg:$((${#kw}+1))}"   # +1 for the leading "["
                msg="${msg#\]}"
                msg="${msg#:}"
                msg="${msg# }"
                break
            fi
        done
        msg="${msg:0:120}"
    fi

    REPLY_LEVEL="$level"
    REPLY_MSG="$msg"
}

process_input() {
    local line
    while IFS= read -r line; do
        [[ -z "$line" ]] && continue
        classify_line "$line"
        printf '%s\t%s\n' "$REPLY_LEVEL" "$REPLY_MSG"
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
    (( total_lines++ )) || true
    lvl_ord=${LEVEL_ORDER[$lvl]:-99}
    if (( lvl_ord >= min_order )); then
        lvl_key="${lvl:-UNKNOWN}"
        (( level_count[$lvl_key]++ )) || true
    fi
    # Bucket message by level for top-N. Still one append per line (needed --
    # this is genuine I/O, not avoidable forking), but no subshell is forked
    # to produce $msg/$lvl any more, which was the actual bottleneck.
    echo "$msg" >> "$TMPDIR_WORK/${lvl}.msgs" 2>/dev/null || true
done < "$ALL_LINES"

# ---- Phase 3: rank top messages per level ------------------------------------
declare -A top_msgs
for lvl in DEBUG INFO WARN ERROR; do
    f="$TMPDIR_WORK/${lvl}.msgs"
    if [[ -f "$f" && -s "$f" ]]; then
        top_msgs[$lvl]=$( { sort "$f" | uniq -c | sort -rn | head -n "$TOP_N" | \
            awk '{count=$1; $1=""; printf "      %5d x %s\n", count, $0}'; } || true )
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
    echo "+==========================================================+"
    echo "|                   logscout_v2  summary                   |"
    echo "+==========================================================+"
    printf "|  %-20s %8s  (%s min-level filter)  |\n" \
        "Total lines:" "$total_lines" "$MIN_LEVEL"
    echo "+==========================================================+"
    printf "|  %-12s  %8d                                 |\n" "ERROR"   "${level_count[ERROR]}"
    printf "|  %-12s  %8d                                 |\n" "WARN"    "${level_count[WARN]}"
    printf "|  %-12s  %8d                                 |\n" "INFO"    "${level_count[INFO]}"
    printf "|  %-12s  %8d                                 |\n" "DEBUG"   "${level_count[DEBUG]}"
    printf "|  %-12s  %8d                                 |\n" "UNKNOWN" "${level_count[UNKNOWN]}"
    echo "+==========================================================+"

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

LOGSCOUT_V2_EOF

chmod +x paper1-shell/newtool/logscout_v2.sh
echo "Created and made executable: paper1-shell/newtool/logscout_v2.sh"
