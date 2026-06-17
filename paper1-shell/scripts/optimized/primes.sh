#!/usr/bin/env bash
# primes (optimized)
# Optimization: replace trial-division with subshell per candidate O(N*sqrt(N)
# subshells) with the Sieve of Eratosthenes using a bash array — O(N log log N)
# arithmetic operations, zero subshells.

N="${1:-100}"

if ! [[ "$N" =~ ^[0-9]+$ ]] || [ "$N" -lt 2 ]; then
    echo "Usage: primes <integer >= 2>" >&2; exit 1
fi

# sieve[i]=1 means i is prime; initialise all to 1
declare -a sieve
for (( i=0; i<=N; i++ )); do sieve[$i]=1; done
sieve[0]=0; sieve[1]=0

for (( p=2; p*p<=N; p++ )); do
    if (( sieve[p] )); then
        for (( m=p*p; m<=N; m+=p )); do
            sieve[$m]=0
        done
    fi
done

count=0
prime_list=""
for (( n=2; n<=N; n++ )); do
    if (( sieve[n] )); then
        prime_list+=" $n"
        (( count++ ))
    fi
done

echo "Primes up to $N:$prime_list"
echo "Total: $count"
