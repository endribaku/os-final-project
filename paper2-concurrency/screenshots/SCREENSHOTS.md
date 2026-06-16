# Paper 2 — Simulation screenshots playbook

The PDF asks for "all simulation screenshots" and "screenshots runs". This file
lists the six demo commands to run on the Ubuntu VM, the output to capture,
and the expected PNG filename. Each run is intentionally short (~1 second)
because the program's *output format* — throughput JSON, meal counts, time -v
table — is identical at any scale.

## Procedure

1. Boot the Ubuntu 24.04 VM.
2. `cd ~/os-final-project` (or wherever the repo lives on the VM).
3. Build binaries once:
   ```bash
   make -C paper2-concurrency/pc/pthreads
   make -C paper2-concurrency/dp/pthreads
   javac paper2-concurrency/pc/java/*.java
   javac paper2-concurrency/dp/java/*.java
   ```
4. For each shot below: run the command in a Terminal, press **`PrtSc`**
   (or use *Screenshot → Active Window*) to capture the Terminal window,
   save the PNG to `paper2-concurrency/screenshots/` with the suggested filename.

## Shots

### 01 — Producer–Consumer, C / POSIX pthreads
```bash
./paper2-concurrency/pc/pthreads/producer_consumer \
    --N 16 --M 4 --K 4 --items 1000 \
    --producer-delay-us 0 --consumer-delay-us 0
```
Capture as: `01-pc-c-pthreads.png` — shows the throughput JSON line.

### 02 — Producer–Consumer, Java monitor
```bash
java -cp paper2-concurrency/pc/java ProducerConsumer \
    --N 16 --M 4 --K 4 --items 1000 \
    --producer-delay-us 0 --consumer-delay-us 0
```
Capture as: `02-pc-java-monitor.png`.

### 03 — Producer–Consumer, Java lock-free (Vyukov)
```bash
java -cp paper2-concurrency/pc/java ProducerConsumerLockFree \
    --N 16 --M 4 --K 4 --items 1000 \
    --producer-delay-us 0 --consumer-delay-us 0
```
Capture as: `03-pc-java-lockfree.png` — visually contrasts against #2.

### 04 — Dining Philosophers, C monitor (dphil_5)
```bash
./paper2-concurrency/dp/pthreads/dphil_5 \
    --N 5 --duration-sec 2 \
    --think-min-ms 10 --think-max-ms 50 \
    --eat-min-ms 10 --eat-max-ms 50 --seed 1
```
Capture as: `04-dp-c-monitor.png` — shows total meals + per-philosopher counts.

### 05 — Sweep driver progress
```bash
PYTHONPATH=. python3 paper2-concurrency/drivers/sweep_pc.py
```
Let it print a few `[run]` lines, then `Ctrl+C`.
Capture as: `05-sweep-pc-progress.png`.

### 06 — GNU `time -v` resource report
```bash
/usr/bin/time -v ./paper2-concurrency/pc/pthreads/producer_consumer \
    --N 64 --M 4 --K 4 --items 5000 \
    --producer-delay-us 0 --consumer-delay-us 0
```
Capture as: `06-time-v-output.png` — shows wall time, CPU %, RSS, context switches
(the exact metrics §4.2 of the paper describes).

## After capturing

Drop all six PNGs into this folder. Then on your Mac, regenerate the docx:

```bash
cd paper2-concurrency/report
pandoc paper2.md -o paper2.docx --resource-path=.:.. \
       --reference-doc=../../config/reference-10pt.docx \
       --syntax-highlighting=none
```

The Appendix E section in `paper2.md` (added once the PNGs land) will embed
them automatically.
