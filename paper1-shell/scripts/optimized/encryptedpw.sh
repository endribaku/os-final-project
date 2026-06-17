#!/usr/bin/env bash
# encryptedpw (optimized)
# Optimization: replace the per-character loop + `od` subshell (O(n) subshells)
# with a single `tr` invocation that handles the full alphabet in one C-level
# pass — O(1) subshells regardless of input length.

SHIFT=${ENCPW_SHIFT:-13}

[ $# -lt 2 ] && { echo "Usage: encryptedpw <encrypt|decrypt> <text>" >&2; exit 1; }

MODE="$1"
TEXT="$2"

if [ "$MODE" != "encrypt" ] && [ "$MODE" != "decrypt" ]; then
    echo "Error: mode must be 'encrypt' or 'decrypt'" >&2; exit 1
fi

# Build tr alphabets shifted by SHIFT positions
build_tr_alphabet() {
    local shift=$1
    # upper/lower source and rotated target via python helper (POSIX tr can't
    # handle arbitrary offsets portably, so we pre-compute the mapping once)
    python3 -c "
import sys
sh = $shift % 26
upper = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
lower = 'abcdefghijklmnopqrstuvwxyz'
ru = upper[sh:] + upper[:sh]
rl = lower[sh:] + lower[:sh]
print(upper + lower)
print(ru + rl)
"
}

if [ "$MODE" = "encrypt" ]; then
    read -r src dst < <(build_tr_alphabet "$SHIFT" | paste - -)
else
    reverse=$(( 26 - SHIFT % 26 ))
    read -r src dst < <(build_tr_alphabet "$reverse" | paste - -)
fi

echo "$TEXT" | tr "$src" "$dst"
