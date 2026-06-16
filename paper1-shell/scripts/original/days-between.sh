#!/usr/bin/env bash
# days-between -- compute the number of days between two dates
# Usage: days-between <MM/DD/YYYY> <MM/DD/YYYY>

usage() {
    echo "Usage: days-between <MM/DD/YYYY> <MM/DD/YYYY>" >&2
    exit 1
}

[ $# -ne 2 ] && usage

# Parse MM/DD/YYYY into components
parse_date() {
    local raw="$1"
    if ! echo "$raw" | grep -qE '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'; then
        echo "Error: invalid date '$raw'. Use MM/DD/YYYY." >&2
        exit 1
    fi
    local mm dd yyyy
    mm=$(echo "$raw" | cut -d'/' -f1)
    dd=$(echo "$raw" | cut -d'/' -f2)
    yyyy=$(echo "$raw" | cut -d'/' -f3)
    printf '%s-%02d-%02d' "$yyyy" "$mm" "$dd"
}

iso1=$(parse_date "$1")
iso2=$(parse_date "$2")

epoch1=$(date -d "$iso1" +%s 2>/dev/null)
epoch2=$(date -d "$iso2" +%s 2>/dev/null)

if [ -z "$epoch1" ] || [ -z "$epoch2" ]; then
    echo "Error: could not convert dates. Make sure you are on Linux (GNU date)." >&2
    exit 1
fi

diff_s=$(( epoch2 - epoch1 ))
days=$(( diff_s / 86400 ))

# Absolute value
if [ "$days" -lt 0 ]; then
    days=$(( -days ))
    earlier="$2"
    later="$1"
else
    earlier="$1"
    later="$2"
fi

echo "From:         $1"
echo "To:           $2"
echo "Days between: $days"
