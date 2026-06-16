#!/usr/bin/env bash
# game_of_life (optimized)
# Key optimization: the original calls `count_neighbors` via command substitution
# `nbrs=$(count_neighbors ...)` which forks a subshell for every cell every
# generation — O(ROWS * COLS * GENS) forks.
# Fix: rewrite count_neighbors to set a global variable instead of printing,
# so it runs in the current shell with zero forks.

GENS="${1:-10}"
ROWS="${2:-20}"
COLS="${3:-40}"
SEED="${4:-42}"

RANDOM=$SEED

declare -a cell
for (( r=0; r<ROWS; r++ )); do
    for (( c=0; c<COLS; c++ )); do
        (( RANDOM % 10 < 3 )) && cell[$(( r*COLS+c ))]=1 || cell[$(( r*COLS+c ))]=0
    done
done

# Sets global _nbr_count — no subshell
_nbr_count=0
count_neighbors() {
    local r=$1 c=$2 nr nc
    _nbr_count=0
    for dr in -1 0 1; do
        for dc in -1 0 1; do
            (( dr == 0 && dc == 0 )) && continue
            (( nr = (r + dr + ROWS) % ROWS ))
            (( nc = (c + dc + COLS) % COLS ))
            (( _nbr_count += cell[nr*COLS+nc] ))
        done
    done
}

print_grid() {
    local gen=$1 row_str
    echo "=== Generation $gen ==="
    for (( r=0; r<ROWS; r++ )); do
        row_str=""
        for (( c=0; c<COLS; c++ )); do
            (( cell[r*COLS+c] )) && row_str+="#" || row_str+="."
        done
        echo "$row_str"
    done
}

declare -a next_cell

for (( gen=0; gen<GENS; gen++ )); do
    print_grid "$gen"
    for (( r=0; r<ROWS; r++ )); do
        for (( c=0; c<COLS; c++ )); do
            local idx=$(( r*COLS+c ))
            count_neighbors "$r" "$c"       # sets _nbr_count in-process
            local alive=${cell[$idx]}
            if (( alive )); then
                (( _nbr_count < 2 || _nbr_count > 3 )) && next_cell[$idx]=0 || next_cell[$idx]=1
            else
                (( _nbr_count == 3 )) && next_cell[$idx]=1 || next_cell[$idx]=0
            fi
        done
    done
    for (( i=0; i<ROWS*COLS; i++ )); do cell[$i]=${next_cell[$i]}; done
done
