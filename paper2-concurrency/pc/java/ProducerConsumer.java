/*
 * Producer–Consumer with a bounded buffer, MONITOR variant.
 * Java intrinsic monitor: `synchronized` + `wait`/`notifyAll`.
 *
 * This is the first of three Java variants we'll implement for Paper 2's
 * "locks vs monitors vs semaphores" comparison. The other two (Semaphore /
 * ReentrantLock+Condition) will live in sibling files.
 *
 * Build:
 *     javac ProducerConsumer.java
 *
 * Run:
 *     java ProducerConsumer --N 64 --M 4 --K 4 --items 10000
 *
 * CLI flags (defaults shown):
 *     --N <buf>                  bounded-buffer size                (64)
 *     --M <producers>            number of producer threads         (1)
 *     --K <consumers>            number of consumer threads         (1)
 *     --items <per-producer>     items each producer pushes         (10000)
 *     --producer-delay-us <us>   per-item busy-wait at producer     (0)
 *     --consumer-delay-us <us>   per-item busy-wait at consumer     (0)
 *     --help                     print this and exit
 *
 * Output: one JSON-ish line on stdout with all app-level metrics.
 * System-level metrics (CPU%, RSS, context switches) come from running
 * this under common/bench.py, which wraps GNU /usr/bin/time -v.
 */
import java.util.ArrayList;
import java.util.Arrays;
import java.util.concurrent.CountDownLatch;

public class ProducerConsumer {

    /** Poison-pill value pushed once per consumer after producers finish. */
    static final long POISON = -1L;

    /**
     * Classic monitor-style bounded buffer. All state guarded by `this`'s
     * intrinsic lock; threads block on `wait()` and wake each other with
     * `notifyAll()`. We store the producer's nanoTime so the consumer can
     * compute end-to-end latency.
     */
    static class BoundedBuffer {
        private final long[] buf;
        private int head = 0, tail = 0, count = 0;

        BoundedBuffer(int capacity) {
            this.buf = new long[capacity];
        }

        synchronized void put(long v) throws InterruptedException {
            while (count == buf.length) wait();
            buf[tail] = v;
            tail = (tail + 1) % buf.length;
            count++;
            notifyAll();
        }

        synchronized long take() throws InterruptedException {
            while (count == 0) wait();
            long v = buf[head];
            head = (head + 1) % buf.length;
            count--;
            notifyAll();
            return v;
        }
    }

    public static void main(String[] args) throws Exception {
        // ---- parse args ----
        int N = 64, M = 1, K = 1, items = 10_000;
        long pDelayUs = 0, cDelayUs = 0;

        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--N", "-N" -> N = Integer.parseInt(args[++i]);
                case "--M", "-M" -> M = Integer.parseInt(args[++i]);
                case "--K", "-K" -> K = Integer.parseInt(args[++i]);
                case "--items" -> items = Integer.parseInt(args[++i]);
                case "--producer-delay-us" -> pDelayUs = Long.parseLong(args[++i]);
                case "--consumer-delay-us" -> cDelayUs = Long.parseLong(args[++i]);
                case "--help", "-h" -> {
                    System.err.println(
                        "Usage: ProducerConsumer [--N buf] [--M producers] [--K consumers] "
                      + "[--items per-producer] [--producer-delay-us us] [--consumer-delay-us us]");
                    return;
                }
                default -> {
                    System.err.println("Unknown arg: " + args[i]);
                    System.exit(2);
                }
            }
        }

        final int bufSize = N;
        final int producers = M;
        final int consumers = K;
        final int itemsEach = items;
        final long pDelayNs = pDelayUs * 1_000L;
        final long cDelayNs = cDelayUs * 1_000L;

        // ---- run ----
        final BoundedBuffer buf = new BoundedBuffer(bufSize);
        final CountDownLatch produced = new CountDownLatch(producers);
        final long[][] latencyArrays = new long[consumers][];
        final Thread[] prodThreads = new Thread[producers];
        final Thread[] consThreads = new Thread[consumers];

        final long startNs = System.nanoTime();

        for (int i = 0; i < producers; i++) {
            prodThreads[i] = new Thread(() -> {
                try {
                    for (int j = 0; j < itemsEach; j++) {
                        if (pDelayNs > 0) busyWait(pDelayNs);
                        buf.put(System.nanoTime());
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    produced.countDown();
                }
            }, "producer-" + i);
            prodThreads[i].start();
        }

        for (int c = 0; c < consumers; c++) {
            final int idx = c;
            consThreads[c] = new Thread(() -> {
                ArrayList<Long> mine = new ArrayList<>();
                try {
                    while (true) {
                        long v = buf.take();
                        if (v == POISON) break;
                        mine.add(System.nanoTime() - v);
                        if (cDelayNs > 0) busyWait(cDelayNs);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
                long[] arr = new long[mine.size()];
                for (int k = 0; k < arr.length; k++) arr[k] = mine.get(k);
                latencyArrays[idx] = arr;
            }, "consumer-" + c);
            consThreads[c].start();
        }

        // wait for producers, then signal consumers to drain & exit
        produced.await();
        for (int i = 0; i < consumers; i++) buf.put(POISON);
        for (Thread t : consThreads) t.join();

        final long endNs = System.nanoTime();

        // ---- aggregate metrics ----
        long total = 0;
        for (long[] a : latencyArrays) total += a.length;

        long[] all = new long[(int) total];
        int p = 0;
        for (long[] a : latencyArrays) {
            System.arraycopy(a, 0, all, p, a.length);
            p += a.length;
        }
        Arrays.sort(all);

        double wallMs = (endNs - startNs) / 1e6;
        double throughputPerSec = total / (wallMs / 1000.0);
        double meanUs = all.length == 0 ? 0.0 : meanNs(all) / 1000.0;
        double p50Us = percentileNs(all, 0.50) / 1000.0;
        double p95Us = percentileNs(all, 0.95) / 1000.0;
        double p99Us = percentileNs(all, 0.99) / 1000.0;
        double maxUs = all.length == 0 ? 0.0 : all[all.length - 1] / 1000.0;

        // single-line, easy to parse from Python (json.loads after a strip)
        System.out.printf(
            "{\"impl\":\"java-monitor\",\"N\":%d,\"M\":%d,\"K\":%d,"
          + "\"items_per_producer\":%d,\"producer_delay_us\":%d,\"consumer_delay_us\":%d,"
          + "\"wall_time_ms\":%.3f,\"items_consumed\":%d,\"throughput_per_sec\":%.2f,"
          + "\"latency_mean_us\":%.3f,\"latency_p50_us\":%.3f,\"latency_p95_us\":%.3f,"
          + "\"latency_p99_us\":%.3f,\"latency_max_us\":%.3f}%n",
            bufSize, producers, consumers, itemsEach, pDelayUs, cDelayUs,
            wallMs, total, throughputPerSec,
            meanUs, p50Us, p95Us, p99Us, maxUs
        );
    }

    private static long meanNs(long[] a) {
        long s = 0;
        for (long v : a) s += v;
        return s / a.length;
    }

    /** Nearest-rank percentile on a pre-sorted array. */
    private static long percentileNs(long[] sorted, double p) {
        if (sorted.length == 0) return 0;
        int idx = (int) Math.ceil(p * sorted.length) - 1;
        if (idx < 0) idx = 0;
        if (idx >= sorted.length) idx = sorted.length - 1;
        return sorted[idx];
    }

    /** Busy-wait for a number of nanoseconds (keeps the thread on-CPU, simulating work). */
    private static void busyWait(long ns) {
        long start = System.nanoTime();
        while (System.nanoTime() - start < ns) { /* spin */ }
    }
}
