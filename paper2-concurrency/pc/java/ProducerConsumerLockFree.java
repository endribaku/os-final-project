/*
 * Producer-Consumer, LOCK-FREE MPMC variant. Paper 2 §8 "Optimization Proposal".
 *
 * Implements a Vyukov-style multi-producer/multi-consumer bounded ring buffer
 * with atomic CAS on the enqueue/dequeue positions and per-cell sequence
 * numbers. There are NO mutexes, condition variables or semaphores — under
 * contention, producers and consumers spin (with `Thread.onSpinWait()` to
 * hint the CPU) rather than block.
 *
 *   Vyukov, "Bounded MPMC queue", 1024cores.net.
 *
 * Expected behaviour vs the monitor variant (ProducerConsumer.java):
 *   - higher throughput under heavy contention (no kernel blocking)
 *   - lower wakeup latency (no condition-variable round-trip)
 *   - SAME OR LOWER context-switch counts
 *   - HIGHER CPU% (busy-wait when empty/full)
 *
 * Constraint: buffer capacity is rounded up to the next power of two so the
 * cell index can be a single AND with a mask. Additionally, capacity is
 * clamped to a minimum of 2: with capacity == 1 the Vyukov sequence-number
 * scheme degenerates (post-enqueue and post-dequeue sequence values become
 * equal for the single slot, allowing a producer to race past an unread
 * value). The effective capacity is reported as `effective_N` in the JSON.
 *
 * CLI is identical to ProducerConsumer.java so sweep_pc.py / plot_pc.py
 * treat both uniformly.
 *
 * Build:  javac ProducerConsumerLockFree.java
 * Run:    java ProducerConsumerLockFree --N 64 --M 4 --K 4 --items 10000
 */
import java.util.ArrayList;
import java.util.Arrays;
import java.util.OptionalLong;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;

public class ProducerConsumerLockFree {

    static final long POISON = -1L;

    /** Vyukov MPMC bounded queue. Capacity must be a power of two. */
    static final class MPMCQueue {

        private static final class Cell {
            final AtomicLong sequence = new AtomicLong();
            /* volatile is enough: writers publish via cell.sequence.set(),
             * readers observe via cell.sequence.get() — those create the
             * happens-before edge that orders the value read/write. */
            volatile long value;
        }

        private final Cell[] buffer;
        private final int    mask;
        private final AtomicLong enqueuePos = new AtomicLong(0);
        private final AtomicLong dequeuePos = new AtomicLong(0);

        MPMCQueue(int requestedCapacity) {
            // Clamp to >= 2 before rounding: cap == 1 breaks the algorithm
            // (post-enq seq == post-deq seq for the single slot).
            int cap = Math.max(2, roundUpPow2(requestedCapacity));
            this.buffer = new Cell[cap];
            this.mask   = cap - 1;
            for (int i = 0; i < cap; i++) {
                Cell c = new Cell();
                c.sequence.set(i);
                buffer[i] = c;
            }
        }

        int capacity() { return mask + 1; }

        boolean tryEnqueue(long value) {
            long pos = enqueuePos.get();
            for (;;) {
                Cell cell = buffer[(int) (pos & mask)];
                long seq = cell.sequence.get();
                long diff = seq - pos;
                if (diff == 0) {
                    if (enqueuePos.compareAndSet(pos, pos + 1)) {
                        cell.value = value;
                        cell.sequence.set(pos + 1);   // publish
                        return true;
                    }
                } else if (diff < 0) {
                    return false;                     // queue full
                } else {
                    pos = enqueuePos.get();
                }
            }
        }

        OptionalLong tryDequeue() {
            long pos = dequeuePos.get();
            for (;;) {
                Cell cell = buffer[(int) (pos & mask)];
                long seq = cell.sequence.get();
                long diff = seq - (pos + 1);
                if (diff == 0) {
                    if (dequeuePos.compareAndSet(pos, pos + 1)) {
                        long v = cell.value;
                        cell.sequence.set(pos + mask + 1);  // free the slot
                        return OptionalLong.of(v);
                    }
                } else if (diff < 0) {
                    return OptionalLong.empty();      // queue empty
                } else {
                    pos = dequeuePos.get();
                }
            }
        }
    }

    /** Smallest power of two >= n (with n >= 1). */
    static int roundUpPow2(int n) {
        if (n < 1) return 1;
        int p = Integer.highestOneBit(n - 1) << 1;
        return p > 0 ? p : 1;
    }

    public static void main(String[] args) throws Exception {
        int  N = 64, M = 1, K = 1, items = 10_000;
        long pDelayUs = 0, cDelayUs = 0;
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--N", "-N" -> N = Integer.parseInt(args[++i]);
                case "--M", "-M" -> M = Integer.parseInt(args[++i]);
                case "--K", "-K" -> K = Integer.parseInt(args[++i]);
                case "--items"   -> items = Integer.parseInt(args[++i]);
                case "--producer-delay-us" -> pDelayUs = Long.parseLong(args[++i]);
                case "--consumer-delay-us" -> cDelayUs = Long.parseLong(args[++i]);
                case "--help", "-h" -> {
                    System.err.println(
                        "Usage: ProducerConsumerLockFree [--N buf] [--M producers] "
                      + "[--K consumers] [--items per-producer] "
                      + "[--producer-delay-us us] [--consumer-delay-us us]");
                    return;
                }
                default -> {
                    System.err.println("Unknown arg: " + args[i]);
                    System.exit(2);
                }
            }
        }

        final int requestedN  = N;
        final MPMCQueue buf   = new MPMCQueue(N);
        final int effectiveN  = buf.capacity();   // rounded up to power of 2
        final int producers   = M;
        final int consumers   = K;
        final int itemsEach   = items;
        final long pDelayNs   = pDelayUs * 1_000L;
        final long cDelayNs   = cDelayUs * 1_000L;

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
                        long ts = System.nanoTime();
                        while (!buf.tryEnqueue(ts)) {
                            Thread.onSpinWait();
                        }
                    }
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
                outer:
                for (;;) {
                    OptionalLong opt = buf.tryDequeue();
                    if (opt.isEmpty()) {
                        Thread.onSpinWait();
                        continue;
                    }
                    long v = opt.getAsLong();
                    if (v == POISON) break outer;
                    mine.add(System.nanoTime() - v);
                    if (cDelayNs > 0) busyWait(cDelayNs);
                }
                long[] arr = new long[mine.size()];
                for (int k = 0; k < arr.length; k++) arr[k] = mine.get(k);
                latencyArrays[idx] = arr;
            }, "consumer-" + c);
            consThreads[c].start();
        }

        produced.await();
        for (int i = 0; i < consumers; i++) {
            while (!buf.tryEnqueue(POISON)) Thread.onSpinWait();
        }
        for (Thread t : consThreads) t.join();

        final long endNs = System.nanoTime();

        // ---- aggregate ----
        long total = 0;
        for (long[] a : latencyArrays) total += a.length;

        long[] all = new long[(int) total];
        int p = 0;
        for (long[] a : latencyArrays) {
            System.arraycopy(a, 0, all, p, a.length);
            p += a.length;
        }
        Arrays.sort(all);

        double wallMs       = (endNs - startNs) / 1e6;
        double throughput   = total / (wallMs / 1000.0);
        double meanUs       = all.length == 0 ? 0.0 : meanNs(all) / 1000.0;
        double p50Us        = percentileNs(all, 0.50) / 1000.0;
        double p95Us        = percentileNs(all, 0.95) / 1000.0;
        double p99Us        = percentileNs(all, 0.99) / 1000.0;
        double maxUs        = all.length == 0 ? 0.0 : all[all.length - 1] / 1000.0;

        System.out.printf(
            "{\"impl\":\"java-lockfree\",\"N\":%d,\"effective_N\":%d,\"M\":%d,\"K\":%d,"
          + "\"items_per_producer\":%d,\"producer_delay_us\":%d,\"consumer_delay_us\":%d,"
          + "\"wall_time_ms\":%.3f,\"items_consumed\":%d,\"throughput_per_sec\":%.2f,"
          + "\"latency_mean_us\":%.3f,\"latency_p50_us\":%.3f,\"latency_p95_us\":%.3f,"
          + "\"latency_p99_us\":%.3f,\"latency_max_us\":%.3f}%n",
            requestedN, effectiveN, producers, consumers, itemsEach, pDelayUs, cDelayUs,
            wallMs, total, throughput,
            meanUs, p50Us, p95Us, p99Us, maxUs
        );
    }

    private static long meanNs(long[] a) {
        long s = 0;
        for (long v : a) s += v;
        return s / a.length;
    }

    private static long percentileNs(long[] sorted, double p) {
        if (sorted.length == 0) return 0;
        int idx = (int) Math.ceil(p * sorted.length) - 1;
        if (idx < 0) idx = 0;
        if (idx >= sorted.length) idx = sorted.length - 1;
        return sorted[idx];
    }

    private static void busyWait(long ns) {
        long start = System.nanoTime();
        while (System.nanoTime() - start < ns) { /* spin */ }
    }
}
