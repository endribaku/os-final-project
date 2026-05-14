/*
 * Implementation of dp_common.h. Shared across dphil_2 / dphil_4 / dphil_5.
 */
#define _POSIX_C_SOURCE 200809L

#include "dp_common.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

volatile int     dp_stop          = 0;
volatile int     dp_deadlocked    = 0;
volatile int64_t dp_last_meal_ns  = 0;

/* ----- args ----- */

void dp_args_init(dp_args_t *a) {
    a->N                  = 5;
    a->duration_sec       = 5.0;
    a->think_min_ms       = 10;
    a->think_max_ms       = 50;
    a->eat_min_ms         = 10;
    a->eat_max_ms         = 50;
    a->seed               = 42;
    a->deadlock_window_ms = 5000;
}

void dp_args_usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s [--N philosophers] [--duration-sec s] "
        "[--think-min-ms ms] [--think-max-ms ms] "
        "[--eat-min-ms ms] [--eat-max-ms ms] "
        "[--seed long] [--deadlock-window-ms ms]\n",
        prog);
}

int dp_args_parse(dp_args_t *a, int argc, char **argv, const char *prog) {
    dp_args_init(a);
    for (int i = 1; i < argc; i++) {
        if      (!strcmp(argv[i], "--N") || !strcmp(argv[i], "-N")) a->N              = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--duration-sec"))                a->duration_sec   = atof(argv[++i]);
        else if (!strcmp(argv[i], "--think-min-ms"))                a->think_min_ms   = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--think-max-ms"))                a->think_max_ms   = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--eat-min-ms"))                  a->eat_min_ms     = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--eat-max-ms"))                  a->eat_max_ms     = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--seed"))                        a->seed           = atol(argv[++i]);
        else if (!strcmp(argv[i], "--deadlock-window-ms"))          a->deadlock_window_ms = atoi(argv[++i]);
        else if (!strcmp(argv[i], "--help") || !strcmp(argv[i], "-h")) {
            dp_args_usage(prog);
            return 1;
        } else {
            fprintf(stderr, "Unknown arg: %s\n", argv[i]);
            dp_args_usage(prog);
            return -1;
        }
    }
    if (a->think_max_ms < a->think_min_ms) a->think_max_ms = a->think_min_ms;
    if (a->eat_max_ms   < a->eat_min_ms)   a->eat_max_ms   = a->eat_min_ms;
    return 0;
}

/* ----- time / sleep ----- */

int64_t dp_now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
}

void dp_sleep_uniform_ms(unsigned *rng_state, int min_ms, int max_ms) {
    int range = max_ms - min_ms;
    int ms    = range <= 0 ? min_ms
                           : min_ms + (int)(rand_r(rng_state) % (unsigned)(range + 1));
    if (ms <= 0) return;
    struct timespec ts = { ms / 1000, (long)(ms % 1000) * 1000000L };
    nanosleep(&ts, NULL);
}

void dp_main_wait(double duration_sec) {
    int64_t deadline = dp_now_ns() + (int64_t)(duration_sec * 1e9);
    while (!dp_stop && dp_now_ns() < deadline) {
        struct timespec ts = { 0, 100L * 1000000L };  /* 100 ms */
        nanosleep(&ts, NULL);
    }
    dp_stop = 1;
}

/* ----- stats ----- */

void phil_stats_init(phil_stats_t *p, int id) {
    p->id       = id;
    p->meals    = 0;
    p->capacity = 1024;
    p->waits_ns = malloc(sizeof(int64_t) * (size_t)p->capacity);
    p->count    = 0;
}

void phil_stats_record(phil_stats_t *p, int64_t wait_ns) {
    p->meals++;
    if (p->count >= p->capacity) {
        p->capacity *= 2;
        p->waits_ns = realloc(p->waits_ns, sizeof(int64_t) * (size_t)p->capacity);
    }
    p->waits_ns[p->count++] = wait_ns;
    dp_last_meal_ns = dp_now_ns();
}

void phil_stats_free(phil_stats_t *p) {
    free(p->waits_ns);
    p->waits_ns = NULL;
}

/* ----- JSON output ----- */

static int cmp_int64(const void *a, const void *b) {
    int64_t x = *(const int64_t *)a, y = *(const int64_t *)b;
    return (x > y) - (x < y);
}

static int64_t percentile_ns(const int64_t *sorted, int n, double p) {
    if (n == 0) return 0;
    int idx = (int)ceil(p * (double)n) - 1;
    if (idx < 0)  idx = 0;
    if (idx >= n) idx = n - 1;
    return sorted[idx];
}

void dp_print_json(const char *impl, const dp_args_t *a, double wall_ms,
                   bool deadlocked, phil_stats_t *stats, int N) {
    long total_meals  = 0;
    int  total_waits  = 0;
    for (int i = 0; i < N; i++) {
        total_meals += stats[i].meals;
        total_waits += stats[i].count;
    }

    int64_t *all = malloc(sizeof(int64_t) * (size_t)(total_waits > 0 ? total_waits : 1));
    int p = 0;
    for (int i = 0; i < N; i++) {
        memcpy(all + p, stats[i].waits_ns, sizeof(int64_t) * (size_t)stats[i].count);
        p += stats[i].count;
    }
    qsort(all, (size_t)total_waits, sizeof(int64_t), cmp_int64);

    int64_t sum_ns = 0;
    for (int i = 0; i < total_waits; i++) sum_ns += all[i];
    double mean_us = total_waits == 0 ? 0.0
                                      : ((double)sum_ns / (double)total_waits) / 1000.0;
    double p50_us  = (double)percentile_ns(all, total_waits, 0.50) / 1000.0;
    double p95_us  = (double)percentile_ns(all, total_waits, 0.95) / 1000.0;
    double p99_us  = (double)percentile_ns(all, total_waits, 0.99) / 1000.0;
    double max_us  = total_waits == 0 ? 0.0
                                      : (double)all[total_waits - 1] / 1000.0;

    printf("{\"impl\":\"%s\",\"N\":%d,\"duration_sec\":%.3f,"
           "\"think_min_ms\":%d,\"think_max_ms\":%d,"
           "\"eat_min_ms\":%d,\"eat_max_ms\":%d,"
           "\"wall_time_ms\":%.3f,\"total_meals\":%ld,"
           "\"meals_per_phil\":[",
           impl, a->N, a->duration_sec,
           a->think_min_ms, a->think_max_ms,
           a->eat_min_ms,   a->eat_max_ms,
           wall_ms, total_meals);
    for (int i = 0; i < N; i++) {
        printf("%s%ld", i == 0 ? "" : ",", stats[i].meals);
    }
    printf("],"
           "\"wait_mean_us\":%.3f,\"wait_p50_us\":%.3f,\"wait_p95_us\":%.3f,"
           "\"wait_p99_us\":%.3f,\"wait_max_us\":%.3f,"
           "\"deadlocked\":%s}\n",
           mean_us, p50_us, p95_us, p99_us, max_us,
           deadlocked ? "true" : "false");
    free(all);
}

/* ----- deadlock watchdog ----- */

void *dp_deadlock_watchdog(void *arg) {
    int     window_ms = *(int *)arg;
    int64_t window_ns = (int64_t)window_ms * 1000000LL;
    while (!dp_stop) {
        struct timespec ts = { 0, 100L * 1000000L };  /* 100 ms */
        nanosleep(&ts, NULL);
        int64_t now = dp_now_ns();
        if (dp_last_meal_ns > 0 && (now - dp_last_meal_ns) > window_ns) {
            dp_deadlocked = 1;
            dp_stop       = 1;
            return NULL;
        }
    }
    return NULL;
}
