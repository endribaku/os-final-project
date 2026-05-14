/*
 * Shared CLI parsing for the three Java dining-philosophers variants.
 * Each variant (DiningMonitor / DiningSemaphore / DiningHierarchy) calls
 * DPArgs.parse(args, "VariantName") and reads the populated fields.
 *
 * Flags (defaults shown):
 *   --N <philosophers>           number of philosophers     (5)
 *   --duration-sec <float>       run duration in seconds    (5.0)
 *   --think-min-ms <int>         lower bound of think delay (10)
 *   --think-max-ms <int>         upper bound of think delay (50)
 *   --eat-min-ms <int>           lower bound of eat delay   (10)
 *   --eat-max-ms <int>           upper bound of eat delay   (50)
 *   --seed <long>                RNG seed (per-thread offset added) (42)
 *   --deadlock-window-ms <int>   watchdog window for naive  (5000; unused by safe variants)
 *   --help, -h                   print usage and exit
 */
import java.util.Random;

public class DPArgs {
    public int N = 5;
    public double durationSec = 5.0;
    public int thinkMinMs = 10, thinkMaxMs = 50;
    public int eatMinMs = 10, eatMaxMs = 50;
    public long seed = 42L;
    public int deadlockWindowMs = 5000;

    public static DPArgs parse(String[] args, String prog) {
        DPArgs a = new DPArgs();
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--N", "-N"           -> a.N = Integer.parseInt(args[++i]);
                case "--duration-sec"      -> a.durationSec = Double.parseDouble(args[++i]);
                case "--think-min-ms"      -> a.thinkMinMs = Integer.parseInt(args[++i]);
                case "--think-max-ms"      -> a.thinkMaxMs = Integer.parseInt(args[++i]);
                case "--eat-min-ms"        -> a.eatMinMs = Integer.parseInt(args[++i]);
                case "--eat-max-ms"        -> a.eatMaxMs = Integer.parseInt(args[++i]);
                case "--seed"              -> a.seed = Long.parseLong(args[++i]);
                case "--deadlock-window-ms"-> a.deadlockWindowMs = Integer.parseInt(args[++i]);
                case "--help", "-h"        -> { usage(prog); System.exit(0); }
                default -> {
                    System.err.println("Unknown arg: " + args[i]);
                    usage(prog);
                    System.exit(2);
                }
            }
        }
        if (a.thinkMaxMs < a.thinkMinMs) a.thinkMaxMs = a.thinkMinMs;
        if (a.eatMaxMs   < a.eatMinMs)   a.eatMaxMs   = a.eatMinMs;
        return a;
    }

    public static void usage(String prog) {
        System.err.println(
            "Usage: " + prog
          + " [--N philosophers] [--duration-sec s] "
          + "[--think-min-ms ms] [--think-max-ms ms] "
          + "[--eat-min-ms ms] [--eat-max-ms ms] "
          + "[--seed long] [--deadlock-window-ms ms]"
        );
    }

    /** Sleep for a uniformly-random duration in [minMs, maxMs] inclusive. */
    public static void sleepBetween(Random rng, int minMs, int maxMs) throws InterruptedException {
        int range = Math.max(0, maxMs - minMs);
        int ms = minMs + (range == 0 ? 0 : rng.nextInt(range + 1));
        if (ms > 0) Thread.sleep(ms);
    }
}
