#!/usr/bin/env bash
# bench_crt.sh -- compare brute-force vs CRT on the configured test cases
# Reads parameters from config/experiments.yaml (parsed with python3).
# Writes timing results to paper1-shell/results/crt_comparison.csv.
#
# Usage: bash bench_crt.sh [reps]  (default: 20)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
CONFIG="$REPO_ROOT/config/experiments.yaml"
RESULTS_DIR="$SCRIPT_DIR/../results"
mkdir -p "$RESULTS_DIR"

REPS="${1:-20}"
CSV="$RESULTS_DIR/crt_comparison.csv"

echo "script,variant,upper_bound,reps,wall_time_s,user_time_s,sys_time_s,cpu_pct,max_rss_kb" > "$CSV"

# Read CRT parameters from YAML
read -r UPPER_BOUND MODULI RESIDUES < <(python3 - <<'PYEOF'
import yaml, sys
cfg = yaml.safe_load(open(sys.argv[1] if len(sys.argv)>1 else "config/experiments.yaml"))
crt = cfg["paper1"]["crt_case_study"]
print(crt["upper_bound"],
      " ".join(str(m) for m in crt["moduli"]),
      " ".join(str(r) for r in crt["residues"]))
PYEOF
)

# Build the argument string: <upper_bound> <m1> <r1> <m2> <r2> ...
ARGS="$UPPER_BOUND"
moduli_arr=($MODULI)
residues_arr=($RESIDUES)
for (( i=0; i<${#moduli_arr[@]}; i++ )); do
    ARGS="$ARGS ${moduli_arr[$i]} ${residues_arr[$i]}"
done

echo "CRT benchmark — args: $ARGS  reps: $REPS"
echo ""

run_bench() {
    local variant="$1"
    local script="$2"
    for (( r=1; r<=REPS; r++ )); do
        /usr/bin/time -v bash "$script" $ARGS 2>/tmp/time_out.txt >/dev/null
        wall=$(grep "Elapsed" /tmp/time_out.txt | awk '{print $NF}' | awk -F: '{if(NF==3)printf "%f", $1*3600+$2*60+$3; else printf "%f", $1*60+$2}')
        user=$(grep "User time" /tmp/time_out.txt | awk '{print $NF}')
        sys=$(grep "System time" /tmp/time_out.txt | awk '{print $NF}')
        cpu=$(grep "Percent of CPU" /tmp/time_out.txt | tr -d '%' | awk '{print $NF}')
        rss=$(grep "Maximum resident" /tmp/time_out.txt | awk '{print $NF}')
        echo "crt,$variant,$UPPER_BOUND,$r,$wall,$user,$sys,$cpu,$rss" >> "$CSV"
        printf "  %s rep %d/%d: %.3fs\n" "$variant" "$r" "$REPS" "$wall"
    done
}

echo "--- Brute force ---"
run_bench "brute" "$SCRIPT_DIR/modular_brute.sh"

echo ""
echo "--- CRT ---"
run_bench "crt" "$SCRIPT_DIR/modular_crt.sh"

echo ""
echo "Results written to: $CSV"
