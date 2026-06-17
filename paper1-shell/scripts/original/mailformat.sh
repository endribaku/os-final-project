#!/usr/bin/env bash
# mailformat -- reformat text/email lines to fit within a given column width
# Usage: mailformat [width] < inputfile
# Default width: 72 (RFC 2822 recommendation)

WIDTH=${1:-72}

while IFS= read -r line; do
    # Preserve blank lines
    if [ -z "$line" ]; then
        echo ""
        continue
    fi

    # Preserve header lines (lines starting with ">" for quoted email)
    if [[ "$line" == ">"* ]]; then
        echo "$line"
        continue
    fi

    current_line=""
    current_len=0

    for word in $line; do
        word_len=${#word}

        if [ "$current_len" -eq 0 ]; then
            current_line="$word"
            current_len="$word_len"
        elif [ $(( current_len + 1 + word_len )) -le "$WIDTH" ]; then
            current_line="$current_line $word"
            current_len=$(( current_len + 1 + word_len ))
        else
            echo "$current_line"
            current_line="$word"
            current_len="$word_len"
        fi
    done

    [ -n "$current_line" ] && echo "$current_line"
done
