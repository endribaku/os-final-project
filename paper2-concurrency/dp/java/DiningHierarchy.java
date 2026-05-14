/*
 * Dining Philosophers, RESOURCE-HIERARCHY variant.
 *
 * Closely follows the Baeldung tutorial cited in the project doc:
 *     https://www.baeldung.com/java-dining-philoshophers
 *
 * Each fork is a plain Object used as an intrinsic-monitor lock. Philosophers
 * always acquire the lower-numbered fork before the higher-numbered fork
 * (a global ordering on resources, equivalent to Baeldung's "last philosopher
 * picks right first" asymmetry). This breaks circular wait => deadlock-free.
 *
 * Build:  javac DiningHierarchy.java
 * Run:    java DiningHierarchy --N 5 --duration-sec 5
 */
import java.util.Random;
import java.util.concurrent.atomic.AtomicLong;

public class DiningHierarchy {

    public static void main(String[] args) throws Exception {
        DPArgs a = DPArgs.parse(args, "DiningHierarchy");
        final int N = a.N;

        Object[] forks = new Object[N];
        for (int i = 0; i < N; i++) forks[i] = new Object();

        DPStats stats = new DPStats(N);
        AtomicLong stop = new AtomicLong(0);

        Thread[] phils = new Thread[N];
        long startNs = System.nanoTime();

        for (int i = 0; i < N; i++) {
            final int idx = i;
            final Random rng = new Random(a.seed + i);

            int leftIdx  = idx;
            int rightIdx = (idx + 1) % N;
            // Global ordering: acquire smaller index first.
            final Object first  = forks[Math.min(leftIdx, rightIdx)];
            final Object second = forks[Math.max(leftIdx, rightIdx)];

            phils[i] = new Thread(() -> {
                try {
                    while (stop.get() == 0) {
                        DPArgs.sleepBetween(rng, a.thinkMinMs, a.thinkMaxMs);

                        long t0 = System.nanoTime();
                        synchronized (first) {
                            synchronized (second) {
                                long waitedNs = System.nanoTime() - t0;
                                DPArgs.sleepBetween(rng, a.eatMinMs, a.eatMaxMs);
                                stats.recordMeal(idx, waitedNs);
                            }
                        }
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
        stats.printJson("java-hierarchy", a, wallMs, /*deadlocked=*/false);
    }
}
