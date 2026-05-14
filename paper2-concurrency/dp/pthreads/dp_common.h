/*
 * Shared CLI parsing, stats collection, JSON output and deadlock watchdog
 * for the three pthreads dining-philosophers variants in this folder
 * (dphil_2 naive, dphil_4 asymmetric, dphil_5 monitor with condvars).
 *
 * Linker symbols dp_stop / dp_deadlocked / dp_last_meal_ns are shared globals
 * (declared `volatile` for visibility; pthreads memory model gives the
 * happens-before we need around lock/unlock and cond signal/wait).
 */
#ifndef DP_COMMON_H
#define DP_COMMON_H

#include <pthread.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct {
    int    N;
    double duration_sec;
    int    think_min_ms, think_max_ms;
    int    eat_min_ms,   eat_max_ms;
    long   seed;
    int    deadlock_window_ms;
} dp_args_t;

void dp_args_init  (dp_args_t *a);
int  dp_args_parse (dp_args_t *a, int argc, char **argv, const char *prog);
void dp_args_usage (const char *prog);

int64_t dp_now_ns (void);
void    dp_sleep_uniform_ms (unsigned *rng_state, int min_ms, int max_ms);

/* Per-philosopher meal + wait-time samples. */
typedef struct {
    int      id;
    long     meals;
    int64_t *waits_ns;    /* dynamic array */
    int      count;
    int      capacity;
} phil_stats_t;

void phil_stats_init   (phil_stats_t *p, int id);
void phil_stats_record (phil_stats_t *p, int64_t wait_ns);
void phil_stats_free   (phil_stats_t *p);

void dp_print_json (const char *impl, const dp_args_t *a, double wall_ms,
                    bool deadlocked, phil_stats_t *stats, int N);

/* Shared run-control flags (see top-of-file note about volatility). */
extern volatile int     dp_stop;
extern volatile int     dp_deadlocked;
extern volatile int64_t dp_last_meal_ns;

/* Watchdog thread fn. arg = (int*) deadlock window in ms. Sets dp_deadlocked
 * and dp_stop if no meal recorded for the window; exits when dp_stop is set. */
void *dp_deadlock_watchdog (void *arg);

/* Bounded sleep: nanosleeps in 100ms chunks until either `duration_sec`
 * elapses or `dp_stop` is observed. Avoids long uninterruptible naps in main. */
void dp_main_wait (double duration_sec);

#endif /* DP_COMMON_H */
