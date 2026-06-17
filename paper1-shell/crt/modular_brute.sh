#!/usr/bin/env bash
# modular_brute.sh -- find x satisfying a system of congruences by brute force
# Usage: modular_brute.sh <upper_bound> <m1> <r1> [<m2> <r2> ...]
# Finds the smallest x in [1, upper_bound] where x ≡ r_i (mod m_i) for all i.
#
# This is the ORIGINAL (section-2a) approach: iterate over every candidate and
# test each modular condition one by one — O(upper_bound * num_congruences).

usage() {
    echo "Usage: modular_brute.sh <upper_bound> <m1> <r1> [<m2> <r2> ...]" >&2
    echo "  Example: modular_brute.sh 10000 5 3 7 4 9 5" >&2
    exit 1
}

[ $# -lt 3 ] && usage
(( ($# - 1) % 2 != 0 )) && { echo "Error: congruences must be given as <modulus> <residue> pairs." >&2; usage; }

UPPER="$1"
shift

# Parse modulus/residue pairs
declare -a moduli=()
declare -a residues=()
while [ $# -gt 0 ]; do
    moduli+=("$1")
    residues+=("$2")
    shift 2
done

num_pairs=${#moduli[@]}

echo "Searching for x in [1, $UPPER] satisfying:"
for (( i=0; i<num_pairs; i++ )); do
    echo "  x ≡ ${residues[$i]}  (mod ${moduli[$i]})"
done
echo ""

found=0
candidates_tested=0

for (( x=1; x<=UPPER; x++ )); do
    candidates_tested=$(( candidates_tested + 1 ))
    ok=1
    for (( i=0; i<num_pairs; i++ )); do
        if [ $(( x % moduli[i] )) -ne "${residues[$i]}" ]; then
            ok=0
            break
        fi
    done
    if [ "$ok" -eq 1 ]; then
        echo "Solution: x = $x"
        found=$(( found + 1 ))
        # Report all solutions up to upper_bound
    fi
done

echo ""
echo "Candidates tested: $candidates_tested"
echo "Solutions found:   $found"
if [ "$found" -eq 0 ]; then
    echo "(No solution in [1, $UPPER])"
fi
