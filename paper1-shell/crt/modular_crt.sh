#!/usr/bin/env bash
# modular_crt.sh -- solve a system of congruences using the Chinese Remainder Theorem
# Usage: modular_crt.sh <upper_bound> <m1> <r1> [<m2> <r2> ...]
#
# Chinese Remainder Theorem (CRT):
#   Given pairwise coprime moduli m_1 … m_k and residues r_1 … r_k,
#   there exists a unique solution x in [0, M) where M = m_1 * m_2 * ... * m_k.
#   The algorithm computes x directly in O(k^2) integer operations — no loop
#   over candidates needed.
#
# Algorithm (constructive CRT):
#   M  = product of all moduli
#   For each i:
#     M_i = M / m_i
#     y_i = modular inverse of M_i mod m_i   (via extended Euclidean algorithm)
#     contribution_i = r_i * M_i * y_i
#   x = (sum of contributions) mod M

usage() {
    echo "Usage: modular_crt.sh <upper_bound> <m1> <r1> [<m2> <r2> ...]" >&2
    echo "  Example: modular_crt.sh 10000 5 3 7 4 9 5" >&2
    exit 1
}

[ $# -lt 3 ] && usage
(( ($# - 1) % 2 != 0 )) && { echo "Error: congruences must be given as modulus/residue pairs." >&2; usage; }

UPPER="$1"
shift

declare -a moduli=()
declare -a residues=()
while [ $# -gt 0 ]; do
    moduli+=("$1")
    residues+=("$2")
    shift 2
done

num_pairs=${#moduli[@]}

echo "Solving system of congruences via CRT:"
for (( i=0; i<num_pairs; i++ )); do
    echo "  x ≡ ${residues[$i]}  (mod ${moduli[$i]})"
done
echo ""

# --- Extended Euclidean Algorithm (returns gcd, s, t  s.t.  a*s + b*t = gcd) ---
# Sets globals: _gcd, _s, _t
extended_gcd() {
    local a=$1 b=$2
    if (( b == 0 )); then
        _gcd=$a; _s=1; _t=0; return
    fi
    extended_gcd "$b" $(( a % b ))
    local old_s=$_s old_t=$_t
    _s=$old_t
    _t=$(( old_s - (a / b) * old_t ))
}

# Modular inverse of a mod m  (requires gcd(a,m)=1)
mod_inverse() {
    local a=$1 m=$2
    extended_gcd "$a" "$m"
    if (( _gcd != 1 )); then
        echo "Error: moduli are not pairwise coprime (gcd($a,$m) = $_gcd)." >&2
        exit 1
    fi
    # Ensure result is positive
    echo $(( (_s % m + m) % m ))
}

# Compute M = product of all moduli
M=1
for (( i=0; i<num_pairs; i++ )); do
    M=$(( M * moduli[i] ))
done

echo "M (product of moduli) = $M"

# Constructive CRT
x_sum=0
for (( i=0; i<num_pairs; i++ )); do
    m_i=${moduli[$i]}
    r_i=${residues[$i]}
    M_i=$(( M / m_i ))
    y_i=$(mod_inverse "$M_i" "$m_i")
    contrib=$(( r_i * M_i * y_i ))
    echo "  i=$i: M_i=$M_i  y_i=$y_i  contrib=$contrib"
    x_sum=$(( x_sum + contrib ))
done

x=$(( x_sum % M ))
(( x <= 0 )) && x=$(( x + M ))

echo ""
echo "CRT solution (smallest positive): x = $x"
echo ""

# Enumerate all solutions up to UPPER_BOUND: x, x+M, x+2M, ...
echo "All solutions in [1, $UPPER]:"
found=0
cur=$x
while (( cur <= UPPER )); do
    (( cur >= 1 )) && { echo "  x = $cur"; (( found++ )); }
    cur=$(( cur + M ))
done

echo ""
echo "Solutions found: $found"
echo "Period (M):      $M"
echo "(Brute-force equivalent would test $UPPER candidates; CRT computed in $num_pairs steps)"
