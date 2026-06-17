#!/usr/bin/env bash
# days-between (optimized)
# Optimizations:
#   1. Replace `echo "$raw" | grep -qE ...` (subshell) with bash `[[ =~ ]]`.
#   2. Replace three `echo "$raw" | cut -d'/' -f<N>` subshells with a single
#      bash IFS split — zero subprocesses for parsing.

[ $# -ne 2 ] && { echo "Usage: days-between <MM/DD/YYYY> <MM/DD/YYYY>" >&2; exit 1; }

parse_date() {
    local raw="$1"
    # Validate with bash regex — no subshell
    if [[ ! "$raw" =~ ^([0-9]{1,2})/([0-9]{1,2})/([0-9]{4})$ ]]; then
        echo "Error: invalid date '$raw'. Use MM/DD/YYYY." >&2; exit 1
    fi
    # BASH_REMATCH already has the groups — no cut/awk needed
    printf '%s-%02d-%02d' "${BASH_REMATCH[3]}" "${BASH_REMATCH[1]}" "${BASH_REMATCH[2]}"
}

iso1=$(parse_date "$1")
iso2=$(parse_date "$2")

epoch1=$(date -d "$iso1" +%s 2>/dev/null)
epoch2=$(date -d "$iso2" +%s 2>/dev/null)

[ -z "$epoch1" ] || [ -z "$epoch2" ] && {
    echo "Error: could not convert dates." >&2; exit 1
}

days=$(( (epoch2 - epoch1) / 86400 ))
(( days < 0 )) && (( days = -days ))

echo "From:         $1"
echo "To:           $2"
echo "Days between: $days"
