#!/usr/bin/env bash
# encryptedpw (instrumented)
LOG_PREFIX="[encryptedpw]"

SHIFT=${ENCPW_SHIFT:-13}

[ $# -lt 2 ] && { echo "Usage: encryptedpw <encrypt|decrypt> <text>" >&2; exit 1; }

MODE="$1"
TEXT="$2"

echo "$LOG_PREFIX START  mode=$MODE  shift=$SHIFT  input_len=${#TEXT}  pid=$$" >&2

if [ "$MODE" != "encrypt" ] && [ "$MODE" != "decrypt" ]; then
    echo "Error: mode must be 'encrypt' or 'decrypt'" >&2
    exit 1
fi

caesar() {
    local input="$1"
    local shift="$2"
    local result=""
    local i char ord new_ord
    local alpha_count=0
    local non_alpha_count=0

    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        ord=$(printf '%s' "$char" | od -An -tu1 | tr -d ' ')
        echo "$LOG_PREFIX   char[$i]='$char' ord=$ord" >&2

        if [ "$ord" -ge 65 ] && [ "$ord" -le 90 ]; then
            new_ord=$(( ( ord - 65 + shift ) % 26 + 65 ))
            alpha_count=$(( alpha_count + 1 ))
        elif [ "$ord" -ge 97 ] && [ "$ord" -le 122 ]; then
            new_ord=$(( ( ord - 97 + shift ) % 26 + 97 ))
            alpha_count=$(( alpha_count + 1 ))
        else
            new_ord=$ord
            non_alpha_count=$(( non_alpha_count + 1 ))
        fi

        result="${result}$(printf "\\$(printf '%03o' "$new_ord")")"
        echo "$LOG_PREFIX   -> new_ord=$new_ord" >&2
    done

    echo "$LOG_PREFIX   alpha_chars=$alpha_count  non_alpha=$non_alpha_count" >&2
    echo "$result"
}

if [ "$MODE" = "encrypt" ]; then
    echo "$LOG_PREFIX encrypting with shift=$SHIFT" >&2
    caesar "$TEXT" "$SHIFT"
else
    reverse=$(( 26 - ( SHIFT % 26 ) ))
    echo "$LOG_PREFIX decrypting with reverse_shift=$reverse" >&2
    caesar "$TEXT" "$reverse"
fi

echo "$LOG_PREFIX END" >&2
