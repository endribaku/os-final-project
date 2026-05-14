/*
 * dphil_2.c -- Dining Philosophers, NAIVE variant (pthreads).
 *
 * Mirrors the UCSB DiningPhil testbed's dphil_2.c. Every philosopher locks
 * its LEFT fork, then its RIGHT fork, with no global ordering and no
 * coordination. Under the right interleaving this hits a classic four-
 * condition deadlock (mutual exclusion + hold-and-wait + no-preemption +
 * circular wait). Useful as the baseline for the "stress test / deadlock
 * frequency" metric required by Paper 2.
 *
 * Detection: a separate watchdog thread (dp_deadlock_watchdog in
 * dp_common.c) checks `dp_last_meal_ns` every 100 ms; if no philosopher has
 * recorded a meal for `--deadlock-window-ms` (default 5000), it flips
 * `dp_deadlocked` and `dp_stop`. On deadlock the philosopher threads are
 * permanently blocked in pthread_mutex_lock, so this main does a hard
 * exit() after emitting the JSON line rather than joining (which would
 * hang forever).
 *
 * Forcing deadlock: shrink the deadlock window and the think jitter, e.g.
 *     ./dphil_2 --N 5 --duration-sec 30 --think-min-ms 0 --think-max-ms 0 \
 *               --eat-min-ms 50 --eat-max-ms 200 --deadlock-window-ms 2000
 *
 * Build:   make
 * Run:     ./dphil_2 --N 5 --duration-sec 5
 */
#include "dp_common.h"

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

static pthread_mutex_t *forks;
static int              g_N;

typedef struct {
    int              id;
    unsigned         rng_state;
    phil_stats_t    *stats;
    const dp_args_t *args;
} phil_arg_t;

static void *philosopher(void *arg) {
    phil_arg_t *pa = (phil_arg_t *)arg;
    int i = pa->id;
    pthread_mutex_t *left_fork  = &forks[i];
    pthread_mutex_t *right_fork = &forks[(i + 1) % g_N];

    while (!dp_stop) {
        dp_sleep_uniform_ms(&pa->rng_state, pa->args->think_min_ms, pa->args->think_max_ms);

        int64_t t0 = dp_now_ns();
        pthread_mutex_lock(left_fork);
        pthread_mutex_lock(right_fork);   /* deadlock can manifest here */
        int64_t waited = dp_now_ns() - t0;

        dp_sleep_uniform_ms(&pa->rng_state, pa->args->eat_min_ms, pa->args->eat_max_ms);

        pthread_mutex_unlock(right_fork);
        pthread_mutex_unlock(left_fork);

        phil_stats_record(pa->stats, waited);
    }
    return NULL;
}

int main(int argc, char **argv) {
    dp_args_t a;
    int rc = dp_args_parse(&a, argc, argv, "dphil_2");
    if (rc != 0) return rc < 0 ? 2 : 0;

    g_N   = a.N;
    forks = malloc(sizeof(pthread_mutex_t) * (size_t)g_N);
    for (int i = 0; i < g_N; i++) pthread_mutex_init(&forks[i], NULL);

    phil_stats_t *stats = malloc(sizeof(phil_stats_t) * (size_t)g_N);
    phil_arg_t   *pargs = malloc(sizeof(phil_arg_t)   * (size_t)g_N);
    pthread_t    *thr   = malloc(sizeof(pthread_t)    * (size_t)g_N);
    for (int i = 0; i < g_N; i++) {
        phil_stats_init(&stats[i], i);
        pargs[i].id        = i;
        pargs[i].rng_state = (unsigned)(a.seed + i);
        pargs[i].stats     = &stats[i];
        pargs[i].args      = &a;
    }

    int64_t start    = dp_now_ns();
    dp_last_meal_ns  = start;

    for (int i = 0; i < g_N; i++)
        pthread_create(&thr[i], NULL, philosopher, &pargs[i]);

    /* Spawn watchdog */
    pthread_t watchdog;
    int       window_ms = a.deadlock_window_ms;
    pthread_create(&watchdog, NULL, dp_deadlock_watchdog, &window_ms);

    /* Wait for duration OR until watchdog flips dp_stop on deadlock. */
    dp_main_wait(a.duration_sec);
    pthread_join(watchdog, NULL);

    double wall_ms = (double)(dp_now_ns() - start) / 1e6;

    if (dp_deadlocked) {
        /* Threads are permanently stuck in pthread_mutex_lock; emit the
         * result and exit hard so we don't deadlock joining. */
        dp_print_json("c-pthreads-naive", &a, wall_ms, /*deadlocked=*/true, stats, g_N);
        fflush(stdout);
        _exit(0);
    }

    for (int i = 0; i < g_N; i++) pthread_join(thr[i], NULL);

    dp_print_json("c-pthreads-naive", &a, wall_ms, /*deadlocked=*/false, stats, g_N);

    for (int i = 0; i < g_N; i++) {
        phil_stats_free(&stats[i]);
        pthread_mutex_destroy(&forks[i]);
    }
    free(forks); free(stats); free(pargs); free(thr);
    return 0;
}
