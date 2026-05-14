/*
 * Shared metric collection + JSON emission for Java dining-philosophers variants.
 *
 * - recordMeal(i, waitNs) is called by philosopher i after acquiring forks,
 *   passing the time it waited from "hungry" to "eating" in nanoseconds.
 * - printJson prints one stable-schema JSON line, matching the schema used
 *   by the C pthreads variants so sweep_dp.py + bench.py can parse them
 *   uniformly.
 */
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

public class DPStats {
    public final int N;
    public final long[] meals;
    private final List<List<Long>> waits;   // waits[i] = nanoseconds samples for philosopher i

    public DPStats(int n) {
        this.N = n;
        this.meals = new long[n];
        this.waits = new ArrayList<>(n);
        for (int i = 0; i < n; i++) waits.add(new ArrayList<>());
    }

    public synchronized void recordMeal(int i, long waitNs) {
        meals[i]++;
        waits.get(i).add(waitNs);
    }

    public void printJson(String impl, DPArgs a, double wallMs, boolean deadlocked) {
        long total = 0;
        for (long m : meals) total += m;

        ArrayList<Long> all = new ArrayList<>();
        for (List<Long> w : waits) all.addAll(w);
        Collections.sort(all);

        double mean = all.isEmpty() ? 0.0
                    : all.stream().mapToLong(Long::longValue).average().orElse(0.0) / 1000.0;
        double p50  = pct(all, 0.50) / 1000.0;
        double p95  = pct(all, 0.95) / 1000.0;
        double p99  = pct(all, 0.99) / 1000.0;
        double max  = all.isEmpty() ? 0.0 : all.get(all.size() - 1) / 1000.0;

        // meals_per_phil as JSON array
        StringBuilder mealsArr = new StringBuilder("[");
        for (int i = 0; i < meals.length; i++) {
            if (i > 0) mealsArr.append(',');
            mealsArr.append(meals[i]);
        }
        mealsArr.append(']');

        System.out.printf(
            "{\"impl\":\"%s\",\"N\":%d,\"duration_sec\":%.3f,"
          + "\"think_min_ms\":%d,\"think_max_ms\":%d,"
          + "\"eat_min_ms\":%d,\"eat_max_ms\":%d,"
          + "\"wall_time_ms\":%.3f,\"total_meals\":%d,"
          + "\"meals_per_phil\":%s,"
          + "\"wait_mean_us\":%.3f,\"wait_p50_us\":%.3f,\"wait_p95_us\":%.3f,"
          + "\"wait_p99_us\":%.3f,\"wait_max_us\":%.3f,"
          + "\"deadlocked\":%s}%n",
            impl, a.N, a.durationSec,
            a.thinkMinMs, a.thinkMaxMs, a.eatMinMs, a.eatMaxMs,
            wallMs, total, mealsArr.toString(),
            mean, p50, p95, p99, max,
            deadlocked ? "true" : "false"
        );
    }

    private static double pct(List<Long> sorted, double p) {
        if (sorted.isEmpty()) return 0.0;
        int idx = (int) Math.ceil(p * sorted.size()) - 1;
        if (idx < 0) idx = 0;
        if (idx >= sorted.size()) idx = sorted.size() - 1;
        return sorted.get(idx);
    }
}
