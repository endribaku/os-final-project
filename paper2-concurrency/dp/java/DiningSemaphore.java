/*
 * Dining Philosophers, SEMAPHORE variant.
 *
 * Each fork is a binary Semaphore. To break circular wait we add a "room"
 * Semaphore initialised to N-1: at most N-1 philosophers may attempt to
 * acquire forks simultaneously. With at least one seat free, the system
 * is deadlock-free (Dijkstra's classic "waiter" formulation).
 *
 * Build:  javac DiningSemaphore.java
 * Run:    java DiningSemaphore --N 5 --duration-sec 5
 */
import java.util.Random;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicLong;

public class DiningSemaphore {

    public static void main(String[] args) throws Exception {
        DPArgs a = DPArgs.parse(args, "DiningSemaphore");
        final int N = a.N;

        Semaphore[] forks = new Semaphore[N];
        for (int i = 0; i < N; i++) forks[i] = new Semaphore(1, /*fair=*/true);
        Semaphore room = new Semaphore(N - 1, /*fair=*/true);

        DPStats stats = new DPStats(N);
        AtomicLong stop = new AtomicLong(0);

        Thread[] phils = new Thread[N];
        long startNs = System.nanoTime();

        for (int i = 0; i < N; i++) {
            final int idx = i;
            final Random rng = new Random(a.seed + i);
            final Semaphore leftFork  = forks[idx];
            final Semaphore rightFork = forks[(idx + 1) % N];
            phils[i] = new Thread(() -> {
                try {
                    while (stop.get() == 0) {
                        DPArgs.sleepBetween(rng, a.thinkMinMs, a.thinkMaxMs);

                        long t0 = System.nanoTime();
                        room.acquire();
                        leftFork.acquire();
                        rightFork.acquire();
                        long waitedNs = System.nanoTime() - t0;

                        DPArgs.sleepBetween(rng, a.eatMinMs, a.eatMaxMs);

                        rightFork.release();
                        leftFork.release();
                        room.release();

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
        stats.printJson("java-semaphore", a, wallMs, /*deadlocked=*/false);
    }
}
