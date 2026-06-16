# VirtualBox Task List — Paper 1

Run these commands **on your Linux VM** (not Windows).
Clone/pull the repo there first, then work from the repo root.

---

## 0. One-time setup

```bash
# Make all scripts executable
chmod +x paper1-shell/scripts/original/*.sh
chmod +x paper1-shell/scripts/instrumented/*.sh
chmod +x paper1-shell/scripts/optimized/*.sh
chmod +x paper1-shell/crt/*.sh
chmod +x paper1-shell/newtool/*.sh

# Verify GNU time is available
/usr/bin/time -v true 2>&1 | grep "Maximum resident"
# If that fails: sudo apt install time

# Install Python deps
pip3 install pyyaml matplotlib numpy pandas
```

---

## 1. Verify scripts run correctly (smoke test)

```bash
# mailformat
echo "This is a very long line that should be wrapped by the mailformat script at 40 columns" | bash paper1-shell/scripts/original/mailformat.sh 40

# collatz
bash paper1-shell/scripts/original/collatz.sh 27
bash paper1-shell/scripts/original/collatz.sh 871

# days-between
bash paper1-shell/scripts/original/days-between.sh "1/1/1900" "1/1/2000"
bash paper1-shell/scripts/original/days-between.sh "6/15/1985" "12/31/2025"

# primes
bash paper1-shell/scripts/original/primes.sh 100

# game_of_life (small, quick)
bash paper1-shell/scripts/original/game_of_life.sh 3 5 10

# tree
bash paper1-shell/scripts/original/tree.sh paper1-shell

# makedict
echo "the quick brown fox jumps over the lazy dog" | bash paper1-shell/scripts/original/makedict.sh

# encryptedpw
bash paper1-shell/scripts/original/encryptedpw.sh encrypt "HelloWorld"
bash paper1-shell/scripts/original/encryptedpw.sh decrypt "$(bash paper1-shell/scripts/original/encryptedpw.sh encrypt HelloWorld)"

# logscout (new tool)
bash paper1-shell/newtool/gen_test_log.sh 200 /tmp/test.log
bash paper1-shell/newtool/logscout.sh /tmp/test.log

# CRT
bash paper1-shell/crt/modular_brute.sh 10000 5 3 7 4 9 5
bash paper1-shell/crt/modular_crt.sh   10000 5 3 7 4 9 5
```

---

## 2. Capture screenshots

Take a terminal screenshot for **each of the 10 scripts** running with a sample input.
Save them as PNG files to `paper1-shell/results/screenshots/`.

```bash
mkdir -p paper1-shell/results/screenshots
# Then run each script visually and screenshot the output.
```

---

## 3. Run instrumented versions and capture logs

```bash
mkdir -p paper1-shell/results/logs

# Example for each script — redirect stderr (log output) to a file
bash paper1-shell/scripts/instrumented/collatz.sh 27 2> paper1-shell/results/logs/collatz_instrumented.log
bash paper1-shell/scripts/instrumented/primes.sh 100 2> paper1-shell/results/logs/primes_instrumented.log
bash paper1-shell/scripts/instrumented/game_of_life.sh 3 5 10 2> paper1-shell/results/logs/game_of_life_instrumented.log
bash paper1-shell/scripts/instrumented/mailformat.sh 40 2> paper1-shell/results/logs/mailformat_instrumented.log < <(echo "This is a test line that is long enough to wrap at forty columns")
bash paper1-shell/scripts/instrumented/encryptedpw.sh encrypt "HelloWorld" 2> paper1-shell/results/logs/encryptedpw_instrumented.log
bash paper1-shell/scripts/instrumented/days-between.sh "1/1/1900" "1/1/2000" 2> paper1-shell/results/logs/days_between_instrumented.log
echo "hello world foo bar" | bash paper1-shell/scripts/instrumented/makedict.sh 2> paper1-shell/results/logs/makedict_instrumented.log
bash paper1-shell/scripts/instrumented/tree.sh paper1-shell 2> paper1-shell/results/logs/tree_instrumented.log
```

---

## 4. Run full benchmark suite (main experiment)

This takes a while (~30–60 min depending on VM speed).

```bash
# From repo root:
python3 paper1-shell/drivers/bench_all.py --reps 20

# To run only a few scripts for a quick test:
python3 paper1-shell/drivers/bench_all.py --reps 5 --scripts collatz primes game_of_life
```

Outputs CSVs to `paper1-shell/results/`.

---

## 5. Run CRT benchmark

```bash
bash paper1-shell/crt/bench_crt.sh 20
# Output: paper1-shell/results/crt_comparison.csv
```

---

## 6. Generate all plots

```bash
python3 paper1-shell/drivers/plot_paper1.py
# Output: paper1-shell/figures/*.png
```

---

## 7. Run strace on key scripts (for I/O analysis section of paper)

```bash
mkdir -p paper1-shell/results/strace

strace -c bash paper1-shell/scripts/original/primes.sh 1000 \
    2> paper1-shell/results/strace/primes_original_strace.txt

strace -c bash paper1-shell/scripts/optimized/primes.sh 1000 \
    2> paper1-shell/results/strace/primes_optimized_strace.txt

strace -c bash paper1-shell/scripts/original/collatz.sh 27114424 \
    2> paper1-shell/results/strace/collatz_original_strace.txt

strace -c bash paper1-shell/scripts/optimized/collatz.sh 27114424 \
    2> paper1-shell/results/strace/collatz_optimized_strace.txt
```

---

## 8. Fill in ENVIRONMENT.md

```bash
echo "## Linux environment" >> ENVIRONMENT.md
uname -a >> ENVIRONMENT.md
lsb_release -a >> ENVIRONMENT.md
bash --version >> ENVIRONMENT.md
python3 --version >> ENVIRONMENT.md
/usr/bin/time --version >> ENVIRONMENT.md 2>&1
```
