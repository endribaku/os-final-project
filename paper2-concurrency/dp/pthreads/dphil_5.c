/*
 * dphil_5.c -- Dining Philosophers, MONITOR variant (pthreads).
 *
 * Maps to the UCSB DiningPhil testbed's dphil_5.c style and to the lecture
 * slide 7.12 monitor solution. State machine over {THINKING, HUNGRY, EATING}
 * guarded by a single mutex; one condition variable per philosopher; a
 * philosopher only enters EATING when neither neighbour is EATING and they
 * themselves are HUNGRY (the classic test()).
 *
 * Build:   make
 * Run:     ./dphil_5 --N 5 --duration-sec 5
 */
#include "dp_common.h"

#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>

enum { THINKING = 0, HUNGRY = 1, EATING = 2 };

static int             *state;
static pthread_mutex_t  monitor_mutex;
static pthread_cond_t  *self;
static int              g_N;

static int left_idx (int i) { return (i - 1 + g_N) % g_N; }
static int right_idx(int i) { return (i + 1) % g_N; }

static void test(int i) {
    if (state[left_idx(i)]  != EATING
     && state[right_idx(i)] != EATING
     && state[i] == HUNGRY) {
        state[i] = EATING;
        pthread_cond_signal(&self[i]);
    }
}

/* Returns 0 on successful acquisition, 1 if shutdown happened first. */
static int pickup(int i) {
    pthread_mutex_lock(&monitor_mutex);
    state[i] = HUNGRY;
    test(i);
    while (state[i] != EATING && !dp_stop) {
        pthread_cond_wait(&self[i], &monitor_mutex);
    }
    int got_it = (state[i] == EATING);
    if (!got_it) state[i] = THINKING;
    pthread_mutex_unlock(&monitor_mutex);
    return got_it ? 0 : 1;
}

static void putdown(int i) {
    pthread_mutex_lock(&monitor_mutex);
    state[i] = THINKING;
    test(left_idx(i));
    test(right_idx(i));
    pthread_mutex_unlock(&monitor_mutex);
}

typedef struct {
    int              id;
    unsigned         rng_state;
    phil_stats_t    *stats;
    const dp_args_t *args;
} phil_arg_t;

static void *philosopher(void *arg) {
    phil_arg_t *pa = (phil_arg_t *)arg;
    while (!dp_stop) {
        dp_sleep_uniform_ms(&pa->rng_state, pa->args->think_min_ms, pa->args->think_max_ms);
        int64_t t0 = dp_now_ns();
        if (pickup(pa->id) != 0) break;
        int64_t waited = dp_now_ns() - t0;
        dp_sleep_uniform_ms(&pa->rng_state, pa->args->eat_min_ms, pa->args->eat_max_ms);
        putdown(pa->id);
        phil_stats_record(pa->stats, waited);
    }
    return NULL;
}

int main(int argc, char **argv) {
    dp_args_t a;
    int rc = dp_args_parse(&a, argc, argv, "dphil_5");
    if (rc != 0) return rc < 0 ? 2 : 0;

    g_N = a.N;
    state = calloc((size_t)g_N, sizeof(int));
    self  = malloc(sizeof(pthread_cond_t) * (size_t)g_N);
    for (int i = 0; i < g_N; i++) pthread_cond_init(&self[i], NULL);
    pthread_mutex_init(&monitor_mutex, NULL);

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

    /* wake any waiters so pickup() can observe dp_stop and return */
    pthread_mutex_lock(&monitor_mutex);
    for (int i = 0; i < g_N; i++) pthread_cond_broadcast(&self[i]);
    pthread_mutex_unlock(&monitor_mutex);

    for (int i = 0; i < g_N; i++) pthread_join(thr[i], NULL);

    double wall_ms = (double)(dp_now_ns() - start) / 1e6;
    dp_print_json("c-pthreads-monitor", &a, wall_ms, /*deadlocked=*/false, stats, g_N);

    for (int i = 0; i < g_N; i++) {
        phil_stats_free(&stats[i]);
        pthread_cond_destroy(&self[i]);
    }
    pthread_mutex_destroy(&monitor_mutex);
    free(state); free(self); free(stats); free(pargs); free(thr);
    return 0;
}
