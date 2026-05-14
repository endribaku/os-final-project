/*
 * Producer-Consumer with a bounded buffer, POSIX pthreads.
 *
 * Structure mirrors the macboypro reference cited by the project doc:
 *     pthread_mutex_t mutex                  -- mutual exclusion on buffer state
 *     sem_t empty                            -- counts free slots (init = N)
 *     sem_t full                             -- counts filled slots (init = 0)
 *
 * Differences from the reference:
 *   - Parameterized N (buffer), M (producers), K (consumers), items-per-producer.
 *   - Clean shutdown via K poison pills + pthread_join (no exit(0) leak).
 *   - Per-item latency tracking with CLOCK_MONOTONIC + percentiles.
 *   - JSON-ish stdout line matching ProducerConsumer.java for uniform parsing.
 *
 * Build:   make                (uses the local Makefile)
 *          or: gcc -O2 -Wall -std=c11 -pthread producer_consumer.c -o producer_consumer -lm
 *
 * Run:     ./producer_consumer --N 64 --M 4 --K 4 --items 10000
 *
 * IMPORTANT: this file uses unnamed POSIX semaphores via sem_init(),
 * which are supported on Linux but deprecated on macOS (sem_init returns
 * ENOSYS). Compile and run inside the Linux VM.
 */
#define _POSIX_C_SOURCE 200809L

#include <math.h>
#include <pthread.h>
#include <semaphore.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

/* -------- globals -------- */

#define POISON ((int64_t)-1)

static int64_t        *buffer;
static int             buf_size;
static int             head = 0, tail = 0;
static pthread_mutex_t mutex;
static sem_t           full_sem;
static sem_t           empty_sem;

static int  g_M = 1, g_K = 1, g_items_each = 10000;
static long g_p_delay_ns = 0, g_c_delay_ns = 0;

/* per-consumer latency collection */
typedef struct {
    int      id;
    int64_t *lat;     /* nanoseconds */
    int      count;
    int      capacity;
} consumer_state_t;

/* -------- helpers -------- */

static int64_t now_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000000000LL + (int64_t)ts.tv_nsec;
}

static void busy_wait_ns(long ns) {
    int64_t start = now_ns();
    while (now_ns() - start < ns) { /* spin */ }
}

static int cmp_int64(const void *a, const void *b) {
    int64_t x = *(const int64_t *)a;
    int64_t y = *(const int64_t *)b;
    return (x > y) - (x < y);
}

/* Nearest-rank percentile on a sorted array. Matches Java's ceil-based formula. */
static int64_t percentile_ns(const int64_t *sorted, int n, double p) {
    if (n == 0) return 0;
    int idx = (int)ceil(p * (double)n) - 1;
    if (idx < 0)  idx = 0;
    if (idx >= n) idx = n - 1;
    return sorted[idx];
}

/* -------- buffer ops (mutex + 2 semaphores, textbook pattern) -------- */

static void buf_put(int64_t v) {
    sem_wait(&empty_sem);
    pthread_mutex_lock(&mutex);
    buffer[tail] = v;
    tail = (tail + 1) % buf_size;
    pthread_mutex_unlock(&mutex);
    sem_post(&full_sem);
}

static int64_t buf_take(void) {
    sem_wait(&full_sem);
    pthread_mutex_lock(&mutex);
    int64_t v = buffer[head];
    head = (head + 1) % buf_size;
    pthread_mutex_unlock(&mutex);
    sem_post(&empty_sem);
    return v;
}

/* -------- threads -------- */

static void *producer_fn(void *arg) {
    (void)arg;
    for (int i = 0; i < g_items_each; i++) {
        if (g_p_delay_ns > 0) busy_wait_ns(g_p_delay_ns);
        buf_put(now_ns());
    }
    return NULL;
}

static void *consumer_fn(void *arg) {
    consumer_state_t *cs = (consumer_state_t *)arg;
    /* expected per-consumer count = M*items / K; allocate a generous initial */
    cs->capacity = (g_M * g_items_each) / g_K + 1024;
    cs->lat = (int64_t *)malloc(sizeof(int64_t) * (size_t)cs->capacity);
    cs->count = 0;

    while (1) {
        int64_t v = buf_take();
        if (v == POISON) break;

        int64_t latency = now_ns() - v;
        if (cs->count >= cs->capacity) {
            cs->capacity *= 2;
            cs->lat = (int64_t *)realloc(cs->lat,
                                         sizeof(int64_t) * (size_t)cs->capacity);
        }
        cs->lat[cs->count++] = latency;

        if (g_c_delay_ns > 0) busy_wait_ns(g_c_delay_ns);
    }
    return NULL;
}

/* -------- main -------- */

static void usage(const char *prog) {
    fprintf(stderr,
        "Usage: %s [--N buf] [--M producers] [--K consumers] "
        "[--items per-producer] [--producer-delay-us us] [--consumer-delay-us us]\n",
        prog);
}

int main(int argc, char **argv) {
    buf_size      = 64;
    g_M           = 1;
    g_K           = 1;
    g_items_each  = 10000;
    long p_delay_us = 0, c_delay_us = 0;

    for (int i = 1; i < argc; i++) {
        if      (strcmp(argv[i], "--N") == 0 || strcmp(argv[i], "-N") == 0) buf_size     = atoi(argv[++i]);
        else if (strcmp(argv[i], "--M") == 0 || strcmp(argv[i], "-M") == 0) g_M          = atoi(argv[++i]);
        else if (strcmp(argv[i], "--K") == 0 || strcmp(argv[i], "-K") == 0) g_K          = atoi(argv[++i]);
        else if (strcmp(argv[i], "--items") == 0)                           g_items_each = atoi(argv[++i]);
        else if (strcmp(argv[i], "--producer-delay-us") == 0)               p_delay_us   = atol(argv[++i]);
        else if (strcmp(argv[i], "--consumer-delay-us") == 0)               c_delay_us   = atol(argv[++i]);
        else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0) { usage(argv[0]); return 0; }
        else { fprintf(stderr, "Unknown arg: %s\n", argv[i]); return 2; }
    }
    g_p_delay_ns = p_delay_us * 1000L;
    g_c_delay_ns = c_delay_us * 1000L;

    /* allocate + init */
    buffer = (int64_t *)malloc(sizeof(int64_t) * (size_t)buf_size);
    if (!buffer)                         { perror("malloc");        return 1; }
    if (pthread_mutex_init(&mutex, NULL) != 0)
                                          { perror("mutex_init");    return 1; }
    if (sem_init(&empty_sem, 0, (unsigned)buf_size) != 0)
                                          { perror("sem_init empty"); return 1; }
    if (sem_init(&full_sem,  0, 0) != 0)  { perror("sem_init full");  return 1; }

    pthread_t        *prods = malloc(sizeof(pthread_t)        * (size_t)g_M);
    pthread_t        *cons  = malloc(sizeof(pthread_t)        * (size_t)g_K);
    consumer_state_t *cs    = malloc(sizeof(consumer_state_t) * (size_t)g_K);
    for (int i = 0; i < g_K; i++) {
        cs[i].id = i; cs[i].lat = NULL; cs[i].count = 0; cs[i].capacity = 0;
    }

    int64_t start = now_ns();

    for (int i = 0; i < g_M; i++) pthread_create(&prods[i], NULL, producer_fn, NULL);
    for (int i = 0; i < g_K; i++) pthread_create(&cons[i],  NULL, consumer_fn, &cs[i]);

    /* wait for producers, then send K poison pills to drain consumers */
    for (int i = 0; i < g_M; i++) pthread_join(prods[i], NULL);
    for (int i = 0; i < g_K; i++) buf_put(POISON);
    for (int i = 0; i < g_K; i++) pthread_join(cons[i], NULL);

    int64_t end = now_ns();

    /* ---- aggregate metrics ---- */
    int total = 0;
    for (int i = 0; i < g_K; i++) total += cs[i].count;

    int64_t *all = (int64_t *)malloc(sizeof(int64_t) * (size_t)(total > 0 ? total : 1));
    int p = 0;
    for (int i = 0; i < g_K; i++) {
        memcpy(all + p, cs[i].lat, sizeof(int64_t) * (size_t)cs[i].count);
        p += cs[i].count;
    }
    qsort(all, (size_t)total, sizeof(int64_t), cmp_int64);

    double  wall_ms        = (double)(end - start) / 1.0e6;
    double  throughput     = total > 0 ? (double)total / (wall_ms / 1000.0) : 0.0;
    int64_t sum_ns         = 0;
    for (int i = 0; i < total; i++) sum_ns += all[i];
    double  mean_us        = total == 0 ? 0.0 : ((double)sum_ns / (double)total) / 1000.0;
    double  p50_us         = (double)percentile_ns(all, total, 0.50) / 1000.0;
    double  p95_us         = (double)percentile_ns(all, total, 0.95) / 1000.0;
    double  p99_us         = (double)percentile_ns(all, total, 0.99) / 1000.0;
    double  max_us         = total == 0 ? 0.0 : (double)all[total - 1] / 1000.0;

    printf("{\"impl\":\"c-pthreads-sem\",\"N\":%d,\"M\":%d,\"K\":%d,"
           "\"items_per_producer\":%d,\"producer_delay_us\":%ld,\"consumer_delay_us\":%ld,"
           "\"wall_time_ms\":%.3f,\"items_consumed\":%d,\"throughput_per_sec\":%.2f,"
           "\"latency_mean_us\":%.3f,\"latency_p50_us\":%.3f,\"latency_p95_us\":%.3f,"
           "\"latency_p99_us\":%.3f,\"latency_max_us\":%.3f}\n",
           buf_size, g_M, g_K, g_items_each, p_delay_us, c_delay_us,
           wall_ms, total, throughput,
           mean_us, p50_us, p95_us, p99_us, max_us);

    /* ---- cleanup ---- */
    for (int i = 0; i < g_K; i++) free(cs[i].lat);
    free(cs); free(prods); free(cons); free(buffer); free(all);
    sem_destroy(&full_sem);
    sem_destroy(&empty_sem);
    pthread_mutex_destroy(&mutex);
    return 0;
}
