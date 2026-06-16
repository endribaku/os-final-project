#!/usr/bin/env bash
# mailformat (instrumented) -- adds timing/logging to expose intermediate work
set -euo pipefail
LOG_PREFIX="[mailformat]"

WIDTH=${1:-72}
echo "$LOG_PREFIX START  width=$WIDTH  pid=$$" >&2

line_count=0
word_count=0
wrap_count=0   # times a line was broken

while IFS= read -r line; do
    line_count=$(( line_count + 1 ))

    if [ -z "$line" ]; then
        echo "$LOG_PREFIX line $line_count: blank" >&2
        echo ""
        continue
    fi

    if [[ "$line" == ">"* ]]; then
        echo "$LOG_PREFIX line $line_count: quoted, passthrough (len=${#line})" >&2
        echo "$line"
        continue
    fi

    echo "$LOG_PREFIX line $line_count: input_len=${#line}" >&2

    current_line=""
    current_len=0
    line_words=0

    for word in $line; do
        word_len=${#word}
        word_count=$(( word_count + 1 ))
        line_words=$(( line_words + 1 ))

        if [ "$current_len" -eq 0 ]; then
            current_line="$word"
            current_len="$word_len"
        elif [ $(( current_len + 1 + word_len )) -le "$WIDTH" ]; then
            current_line="$current_line $word"
            current_len=$(( current_len + 1 + word_len ))
        else
            echo "$LOG_PREFIX   wrap: emitting line of len=$current_len" >&2
            echo "$current_line"
            wrap_count=$(( wrap_count + 1 ))
            current_line="$word"
            current_len="$word_len"
        fi
    done

    if [ -n "$current_line" ]; then
        echo "$LOG_PREFIX   final segment: len=$current_len words=$line_words" >&2
        echo "$current_line"
    fi
done

echo "$LOG_PREFIX END  lines_in=$line_count words=$word_count wraps=$wrap_count" >&2
