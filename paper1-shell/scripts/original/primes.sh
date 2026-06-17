#!/usr/bin/env bash
# primes -- find all prime numbers up to N using trial division
# Usage: primes <N>
# Note: trial division is O(N * sqrt(N)) — intentionally naive for benchmarking.

N="${1:-100}"

if ! [[ "$N" =~ ^[0-9]+$ ]] || [ "$N" -lt 2 ]; then
    echo "Usage: primes <integer >= 2>" >&2
    exit 1
fi

is_prime() {
    local n=$1
    [ "$n" -lt 2 ] && echo 0 && return
    [ "$n" -eq 2 ] && echo 1 && return
    [ $(( n % 2 )) -eq 0 ] && echo 0 && return

    local d=3
    while [ $(( d * d )) -le "$n" ]; do
        [ $(( n % d )) -eq 0 ] && echo 0 && return
        d=$(( d + 2 ))
    done
    echo 1
}

count=0
prime_list=""

for (( n=2; n<=N; n++ )); do
    result=$(is_prime "$n")
    if [ "$result" -eq 1 ]; then
        prime_list="$prime_list $n"
        count=$(( count + 1 ))
    fi
done

echo "Primes up to $N:$prime_list"
echo "Total: $count"
