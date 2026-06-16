#!/usr/bin/env bash
# gen_test_log.sh -- generate a synthetic log file for testing logscout
# Usage: gen_test_log.sh [lines] [outfile]
# Default: 1000 lines to stdout

LINES="${1:-1000}"
OUT="${2:-/dev/stdout}"

LEVELS=(DEBUG DEBUG DEBUG INFO INFO INFO INFO WARN WARN ERROR)
TIMESTAMPS_FMT="%Y-%m-%dT%H:%M:%S"

ERROR_MSGS=(
    "Connection refused on port 5432"
    "Null pointer dereference in module auth"
    "Disk quota exceeded for user www-data"
    "Failed to acquire lock on /var/run/app.pid"
    "Segmentation fault (core dumped)"
)
WARN_MSGS=(
    "Response time exceeded 500ms threshold"
    "Retrying request (attempt 2/3)"
    "Config value 'timeout' not set, using default"
    "Low memory: only 128MB available"
    "Deprecated API endpoint called: /v1/users"
)
INFO_MSGS=(
    "Server started on 0.0.0.0:8080"
    "Request handled successfully"
    "User 42 logged in"
    "Cache miss for key session:abc123"
    "Background job completed in 1.2s"
    "Database connection pool initialized (size=10)"
)
DEBUG_MSGS=(
    "Entering function processRequest"
    "SQL query: SELECT * FROM users WHERE id = ?"
    "HTTP response code: 200"
    "Loaded config from /etc/app/config.yaml"
    "Thread pool size: 4"
)

pick_msg() {
    local arr=("$@")
    echo "${arr[$(( RANDOM % ${#arr[@]} ))]}"
}

{
    for (( i=0; i<LINES; i++ )); do
        ts=$(date -d "$(( RANDOM % 86400 )) seconds" +"$TIMESTAMPS_FMT" 2>/dev/null || date +"$TIMESTAMPS_FMT")
        level="${LEVELS[$(( RANDOM % ${#LEVELS[@]} ))]}"
        case "$level" in
            ERROR) msg=$(pick_msg "${ERROR_MSGS[@]}") ;;
            WARN)  msg=$(pick_msg "${WARN_MSGS[@]}") ;;
            INFO)  msg=$(pick_msg "${INFO_MSGS[@]}") ;;
            DEBUG) msg=$(pick_msg "${DEBUG_MSGS[@]}") ;;
        esac
        echo "$ts $level $msg"
    done
} > "$OUT"

echo "Generated $LINES log lines -> $OUT" >&2
