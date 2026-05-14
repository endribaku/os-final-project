/*
 * dphil_4.c -- Dining Philosophers, ASYMMETRIC / RESOURCE-HIERARCHY variant.
 *
 * Mirrors the UCSB DiningPhil testbed's dphil_4.c. Each fork is a plain
 * pthread_mutex_t. Even-id philosophers acquire their LEFT fork first then
 * the RIGHT; odd-id philosophers acquire RIGHT first then LEFT. This breaks
 * the circular-wait Coffman condition => deadlock-free with raw mutex locks
 * (no condvars, no semaphores).
 *
 * Build:   make
 * Run:     ./dphil_4 --N 5 --duration-sec 5
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
    pthread_mutex_t *first, *second;
    if ((i & 1) == 0) { first = left_fork;  second = right_fork; }
    else              { first = right_fork; second = left_fork;  }

    while (!dp_stop) {
        dp_sleep_uniform_ms(&pa->rng_state, pa->args->think_min_ms, pa->args->think_max_ms);

        int64_t t0 = dp_now_ns();
        pthread_mutex_lock(first);
        pthread_mutex_lock(second);
        int64_t waited = dp_now_ns() - t0;

        dp_sleep_uniform_ms(&pa->rng_state, pa->args->eat_min_ms, pa->args->eat_max_ms);

        pthread_mutex_unlock(second);
        pthread_mutex_unlock(first);

        phil_stats_record(pa->stats, waited);
    }
    return NULL;
}

int main(int argc, char **argv) {
    dp_args_t a;
    int rc = dp_args_parse(&a, argc, argv, "dphil_4");
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

    dp_main_wait(a.duration_sec);

    for (int i = 0; i < g_N; i++) pthread_join(thr[i], NULL);

    double wall_ms = (double)(dp_now_ns() - start) / 1e6;
    dp_print_json("c-pthreads-hierarchy", &a, wall_ms, /*deadlocked=*/false, stats, g_N);

    for (int i = 0; i < g_N; i++) {
        phil_stats_free(&stats[i]);
        pthread_mutex_destroy(&forks[i]);
    }
    free(forks); free(stats); free(pargs); free(thr);
    return 0;
}
