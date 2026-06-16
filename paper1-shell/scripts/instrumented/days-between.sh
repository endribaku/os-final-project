#!/usr/bin/env bash
# days-between (instrumented)
LOG_PREFIX="[days-between]"

[ $# -ne 2 ] && { echo "Usage: days-between <MM/DD/YYYY> <MM/DD/YYYY>" >&2; exit 1; }

echo "$LOG_PREFIX START  date1='$1'  date2='$2'  pid=$$" >&2

parse_date() {
    local raw="$1"
    echo "$LOG_PREFIX   parse_date: '$raw'" >&2

    if ! echo "$raw" | grep -qE '^[0-9]{1,2}/[0-9]{1,2}/[0-9]{4}$'; then
        echo "Error: invalid date '$raw'. Use MM/DD/YYYY." >&2
        exit 1
    fi

    local mm dd yyyy
    mm=$(echo "$raw" | cut -d'/' -f1)
    dd=$(echo "$raw" | cut -d'/' -f2)
    yyyy=$(echo "$raw" | cut -d'/' -f3)

    echo "$LOG_PREFIX   parsed: mm=$mm dd=$dd yyyy=$yyyy" >&2
    printf '%s-%02d-%02d' "$yyyy" "$mm" "$dd"
}

iso1=$(parse_date "$1")
iso2=$(parse_date "$2")

echo "$LOG_PREFIX   iso1=$iso1  iso2=$iso2" >&2

epoch1=$(date -d "$iso1" +%s 2>/dev/null)
epoch2=$(date -d "$iso2" +%s 2>/dev/null)

echo "$LOG_PREFIX   epoch1=$epoch1  epoch2=$epoch2" >&2

if [ -z "$epoch1" ] || [ -z "$epoch2" ]; then
    echo "Error: could not convert dates." >&2
    exit 1
fi

diff_s=$(( epoch2 - epoch1 ))
days=$(( diff_s / 86400 ))
echo "$LOG_PREFIX   diff_s=$diff_s  days_raw=$days" >&2

if [ "$days" -lt 0 ]; then
    days=$(( -days ))
fi

echo "From:         $1"
echo "To:           $2"
echo "Days between: $days"
echo "$LOG_PREFIX END  days=$days" >&2
