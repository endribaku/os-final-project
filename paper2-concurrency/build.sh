#!/usr/bin/env bash
# Compile all Paper 2 code (Java + C pthreads). Idempotent.
#
# Usage: ./paper2-concurrency/build.sh
#
# Run inside the Linux VM. macOS will not link the pthreads code
# because we use unnamed POSIX semaphores via sem_init().

set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo ">>> pc/java"
( cd pc/java && javac *.java )

echo ">>> dp/java"
( cd dp/java && javac *.java )

echo ">>> pc/pthreads"
( cd pc/pthreads && make )

echo ">>> dp/pthreads"
( cd dp/pthreads && make )

echo
echo "[build] done."
echo "  Java classes:"
ls -1 "$HERE"/pc/java/*.class "$HERE"/dp/java/*.class 2>/dev/null | wc -l \
    | awk '{print "    total: " $1}'
echo "  C binaries:"
for bin in "$HERE"/pc/pthreads/producer_consumer \
           "$HERE"/dp/pthreads/dphil_2 \
           "$HERE"/dp/pthreads/dphil_4 \
           "$HERE"/dp/pthreads/dphil_5; do
    if [[ -x "$bin" ]]; then
        printf "    OK  %s\n" "${bin#$HERE/}"
    else
        printf "    MISSING  %s\n" "${bin#$HERE/}" >&2
    fi
done
