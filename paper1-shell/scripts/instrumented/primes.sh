#!/usr/bin/env bash
# primes (instrumented) -- logs every primality test and trial-division steps
LOG_PREFIX="[primes]"

N="${1:-100}"

if ! [[ "$N" =~ ^[0-9]+$ ]] || [ "$N" -lt 2 ]; then
    echo "Usage: primes <integer >= 2>" >&2
    exit 1
fi

echo "$LOG_PREFIX START  N=$N  pid=$$" >&2

total_subshells=0
total_divisions=0

is_prime() {
    local n=$1
    total_subshells=$(( total_subshells + 1 ))
    local divisions=0

    [ "$n" -lt 2 ] && echo 0 && return
    [ "$n" -eq 2 ] && echo 1 && return
    [ $(( n % 2 )) -eq 0 ] && echo 0 && return

    local d=3
    while [ $(( d * d )) -le "$n" ]; do
        divisions=$(( divisions + 1 ))
        total_divisions=$(( total_divisions + 1 ))
        if [ $(( n % d )) -eq 0 ]; then
            echo "$LOG_PREFIX   is_prime($n): composite, divisor=$d  divisions=$divisions" >&2
            echo 0
            return
        fi
        d=$(( d + 2 ))
    done

    echo "$LOG_PREFIX   is_prime($n): PRIME  divisions=$divisions" >&2
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
echo "$LOG_PREFIX END  primes_found=$count  subshell_calls=$total_subshells  divisions=$total_divisions" >&2
