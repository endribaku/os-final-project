#!/usr/bin/env bash
# game_of_life -- Conway's Game of Life in pure Bash
# Usage: game_of_life [generations] [rows] [cols] [seed]
# Prints each generation to stdout (no terminal clearing — suitable for piping/logging).

GENS="${1:-10}"
ROWS="${2:-20}"
COLS="${3:-40}"
SEED="${4:-42}"

RANDOM=$SEED

# Flat array: cell[r*COLS+c] = 0|1
declare -a cell

# Initialise with ~30% random live cells
for (( r=0; r<ROWS; r++ )); do
    for (( c=0; c<COLS; c++ )); do
        if (( RANDOM % 10 < 3 )); then
            cell[$(( r*COLS + c ))]=1
        else
            cell[$(( r*COLS + c ))]=0
        fi
    done
done

count_neighbors() {
    local r=$1 c=$2
    local count=0
    local nr nc idx

    for dr in -1 0 1; do
        for dc in -1 0 1; do
            [ "$dr" -eq 0 ] && [ "$dc" -eq 0 ] && continue
            nr=$(( (r + dr + ROWS) % ROWS ))
            nc=$(( (c + dc + COLS) % COLS ))
            idx=$(( nr*COLS + nc ))
            count=$(( count + cell[idx] ))
        done
    done
    echo $count
}

print_grid() {
    local gen=$1
    echo "=== Generation $gen ==="
    local row_str
    for (( r=0; r<ROWS; r++ )); do
        row_str=""
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

    declare -a next_cell

    for (( r=0; r<ROWS; r++ )); do
        for (( c=0; c<COLS; c++ )); do
            idx=$(( r*COLS + c ))
            nbrs=$(count_neighbors "$r" "$c")
            alive=${cell[$idx]}

            if [ "$alive" -eq 1 ]; then
                if [ "$nbrs" -lt 2 ] || [ "$nbrs" -gt 3 ]; then
                    next_cell[$idx]=0
                else
                    next_cell[$idx]=1
                fi
            else
                if [ "$nbrs" -eq 3 ]; then
                    next_cell[$idx]=1
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
done
