#!/usr/bin/env bash
# encryptedpw -- Caesar-cipher password obfuscator
# Usage: encryptedpw <encrypt|decrypt> <text>
# Uses a configurable shift (default 13 = ROT13, which is self-inverse).
#
# NOTE: This is a demonstration script only — Caesar cipher is NOT secure.
#       It models the kind of simple obfuscation scripts found in sysadmin
#       automation (e.g., hiding a plain-text password from casual observers).

SHIFT=${ENCPW_SHIFT:-13}

usage() {
    echo "Usage: encryptedpw <encrypt|decrypt> <text>" >&2
    echo "  env ENCPW_SHIFT=<n> to change Caesar shift (default 13)" >&2
    exit 1
}

[ $# -lt 2 ] && usage

MODE="$1"
TEXT="$2"

if [ "$MODE" != "encrypt" ] && [ "$MODE" != "decrypt" ]; then
    echo "Error: mode must be 'encrypt' or 'decrypt'" >&2
    usage
fi

caesar() {
    local input="$1"
    local shift="$2"
    local result=""
    local i char ord new_ord

    for (( i=0; i<${#input}; i++ )); do
        char="${input:$i:1}"
        # Get ASCII ordinal via printf + od
        ord=$(printf '%s' "$char" | od -An -tu1 | tr -d ' ')

        if [ "$ord" -ge 65 ] && [ "$ord" -le 90 ]; then
            # Uppercase A-Z
            new_ord=$(( ( ord - 65 + shift ) % 26 + 65 ))
        elif [ "$ord" -ge 97 ] && [ "$ord" -le 122 ]; then
            # Lowercase a-z
            new_ord=$(( ( ord - 97 + shift ) % 26 + 97 ))
        else
            new_ord=$ord
        fi

        result="${result}$(printf "\\$(printf '%03o' "$new_ord")")"
    done

    echo "$result"
}

if [ "$MODE" = "encrypt" ]; then
    caesar "$TEXT" "$SHIFT"
else
    # Decrypt: shift in the opposite direction
    reverse=$(( 26 - ( SHIFT % 26 ) ))
    caesar "$TEXT" "$reverse"
fi
