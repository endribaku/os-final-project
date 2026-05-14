/*
 * Dining Philosophers, MONITOR variant.
 *
 * Direct translation of the lecture solution (transparency 7.12):
 *
 *     monitor DiningPhilosophers {
 *         enum {THINKING, HUNGRY, EATING} state[N];
 *         condition self[N];
 *         void pickup(int i)  { state[i] = HUNGRY; test(i);
 *                               if (state[i] != EATING) self[i].wait(); }
 *         void putdown(int i) { state[i] = THINKING;
 *                               test((i-1+N)%N); test((i+1)%N); }
 *         void test(int i)    { if (state[(i-1+N)%N] != EATING &&
 *                                   state[(i+1)%N]   != EATING &&
 *                                   state[i] == HUNGRY) {
 *                                  state[i] = EATING; self[i].signal(); } }
 *     }
 *
 * Translated to Java as a ReentrantLock + Condition[] (which is the JDK's
 * direct equivalent of the monitor concept; per java.util.concurrent.locks
 * javadoc, a Condition replaces the role of wait/notify on a monitor).
 *
 * CLI is identical to the other dining-philosophers variants in this folder,
 * so the sweep driver and bench.py can treat them uniformly.
 *
 * Build:  javac DiningMonitor.java
 * Run:    java DiningMonitor --N 5 --duration-sec 5
 */
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Random;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.locks.Condition;
import java.util.concurrent.locks.ReentrantLock;

public class DiningMonitor {

    /* ----- monitor state ----- */
    static final int N_THINKING = 0, N_HUNGRY = 1, N_EATING = 2;

    static class Table {
        final int N;
        final int[] state;
        final ReentrantLock lock = new ReentrantLock();
        final Condition[] self;

        Table(int n) {
            this.N = n;
            this.state = new int[n];
            Arrays.fill(state, N_THINKING);
            this.self = new Condition[n];
            for (int i = 0; i < n; i++) self[i] = lock.newCondition();
        }

        int left(int i)  { return (i - 1 + N) % N; }
        int right(int i) { return (i + 1) % N; }

        void pickup(int i) throws InterruptedException {
            lock.lock();
            try {
                state[i] = N_HUNGRY;
                test(i);
                while (state[i] != N_EATING) self[i].await();
            } finally { lock.unlock(); }
        }

        void putdown(int i) {
            lock.lock();
            try {
                state[i] = N_THINKING;
                test(left(i));
                test(right(i));
            } finally { lock.unlock(); }
        }

        private void test(int i) {
            if (state[left(i)] != N_EATING
                && state[right(i)] != N_EATING
                && state[i] == N_HUNGRY) {
                state[i] = N_EATING;
                self[i].signal();
            }
        }
    }

    public static void main(String[] args) throws Exception {
        DPArgs a = DPArgs.parse(args, "DiningMonitor");
        Table table = new Table(a.N);
        DPStats stats = new DPStats(a.N);
        AtomicLong stop = new AtomicLong(0);

        Thread[] phils = new Thread[a.N];
        long startNs = System.nanoTime();

        for (int i = 0; i < a.N; i++) {
            final int idx = i;
            final Random rng = new Random(a.seed + i);
            phils[i] = new Thread(() -> {
                try {
                    while (stop.get() == 0) {
                        DPArgs.sleepBetween(rng, a.thinkMinMs, a.thinkMaxMs);
                        long t0 = System.nanoTime();
                        table.pickup(idx);
                        long waitedNs = System.nanoTime() - t0;
                        DPArgs.sleepBetween(rng, a.eatMinMs, a.eatMaxMs);
                        table.putdown(idx);
                        stats.recordMeal(idx, waitedNs);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "phil-" + i);
            phils[i].start();
        }

        Thread.sleep((long) (a.durationSec * 1000));
        stop.set(1);
        for (Thread t : phils) t.interrupt();
        for (Thread t : phils) t.join();

        double wallMs = (System.nanoTime() - startNs) / 1e6;
        stats.printJson("java-monitor", a, wallMs, /*deadlocked=*/false);
    }
}
