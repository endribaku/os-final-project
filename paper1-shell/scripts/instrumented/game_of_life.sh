#!/usr/bin/env bash
# game_of_life (instrumented) -- logs per-generation stats and neighbor-count calls
LOG_PREFIX="[game_of_life]"

GENS="${1:-10}"
ROWS="${2:-20}"
COLS="${3:-40}"
SEED="${4:-42}"

RANDOM=$SEED

echo "$LOG_PREFIX START  gens=$GENS  rows=$ROWS  cols=$COLS  seed=$SEED  pid=$$" >&2

declare -a cell
live_init=0

for (( r=0; r<ROWS; r++ )); do
    for (( c=0; c<COLS; c++ )); do
        if (( RANDOM % 10 < 3 )); then
            cell[$(( r*COLS + c ))]=1
            live_init=$(( live_init + 1 ))
        else
            cell[$(( r*COLS + c ))]=0
        fi
    done
done

echo "$LOG_PREFIX   initial live cells: $live_init / $(( ROWS*COLS ))" >&2

neighbor_calls=0

count_neighbors() {
    local r=$1 c=$2
    local count=0
    neighbor_calls=$(( neighbor_calls + 1 ))

    for dr in -1 0 1; do
        for dc in -1 0 1; do
            [ "$dr" -eq 0 ] && [ "$dc" -eq 0 ] && continue
            local nr=$(( (r + dr + ROWS) % ROWS ))
            local nc=$(( (c + dc + COLS) % COLS ))
            count=$(( count + cell[$(( nr*COLS + nc ))] ))
        done
    done
    echo $count
}

print_grid() {
    local gen=$1
    echo "=== Generation $gen ==="
    for (( r=0; r<ROWS; r++ )); do
        local row_str=""
        for (( c=0; c<COLS; c++ )); do
            if [ "${cell[$(( r*COLS + c ))]}" -eq 1 ]; then
                row_str="${row_str}#"
            else
                row_str="${row_str}."
            fi
        done
        echo "$row_str"
    done
}

for (( gen=0; gen<GENS; gen++ )); do
    print_grid "$gen"

    live_before=0
    for (( i=0; i<ROWS*COLS; i++ )); do
        live_before=$(( live_before + cell[i] ))
    done

    declare -a next_cell
    births=0
    deaths=0

    for (( r=0; r<ROWS; r++ )); do
        for (( c=0; c<COLS; c++ )); do
            local idx=$(( r*COLS + c ))
            local nbrs
            nbrs=$(count_neighbors "$r" "$c")
            local alive=${cell[$idx]}

            if [ "$alive" -eq 1 ]; then
                if [ "$nbrs" -lt 2 ] || [ "$nbrs" -gt 3 ]; then
                    next_cell[$idx]=0
                    deaths=$(( deaths + 1 ))
                else
                    next_cell[$idx]=1
                fi
            else
                if [ "$nbrs" -eq 3 ]; then
                    next_cell[$idx]=1
                    births=$(( births + 1 ))
                else
                    next_cell[$idx]=0
                fi
            fi
        done
    done

    for (( i=0; i<ROWS*COLS; i++ )); do
        cell[$i]=${next_cell[$i]}
    done
    unset next_cell

    live_after=$(( live_before + births - deaths ))
    echo "$LOG_PREFIX   gen=$gen  live_before=$live_before  births=$births  deaths=$deaths  live_after=$live_after  neighbor_calls_total=$neighbor_calls" >&2
done

echo "$LOG_PREFIX END  total_neighbor_calls=$neighbor_calls" >&2
