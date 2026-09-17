import type { Race } from "./analytics";

const mean = (v: number[]) => v.reduce((a, b) => a + b, 0) / v.length;
const fmt = (v: number, d = 1) => v.toFixed(d);
const minimum = (v: number[]) => v.reduce((a, b) => Math.min(a, b), Infinity);
const maximum = (v: number[]) => v.reduce((a, b) => Math.max(a, b), -Infinity);

function group(rows: Race[], key: (r: Race) => string | number) {
  const m = new Map<string, Race[]>();
  for (const r of rows) {
    const k = String(key(r));
    const g = m.get(k);
    if (g) g.push(r);
    else m.set(k, [r]);
  }
  return [...m].sort((a, b) =>
    a[0].localeCompare(b[0], undefined, { numeric: true }),
  );
}
const avg = (r: Race[]) => mean(r.map((v) => v.w));
const winRate = (r: Race[]) => r.filter((v) => v.r === 1).length / r.length;
const monthly = (rows: Race[]) => group(rows, (r) => r.d.slice(0, 7));
const frequent = (rows: Race[], limit = 5) =>
  group(rows, (r) => r.t)
    .sort((a, b) => b[1].length - a[1].length)
    .slice(0, limit);
const slope = (ys: number[]) => {
  // least-squares slope vs index
  const n = ys.length,
    xm = (n - 1) / 2,
    ym = mean(ys);
  let num = 0,
    den = 0;
  for (let i = 0; i < n; i++) {
    num += (i - xm) * (ys[i] - ym);
    den += (i - xm) ** 2;
  }
  return den ? num / den : 0;
};
const extremes = (groups: [string, Race[]][], value: (r: Race[]) => number) => {
  let lo: [string, number] | null = null,
    hi: [string, number] | null = null;
  for (const [k, rs] of groups) {
    const v = value(rs);
    if (!lo || v < lo[1]) lo = [k, v];
    if (!hi || v > hi[1]) hi = [k, v];
  }
  return { lo, hi };
};

export function calculateInsights(id: string, rows: Race[]): string[] {
  if (!rows.length) return [];
  const n = rows.length;
  const wpms = rows.map((r) => r.w),
    accs = rows.map((r) => r.a);

  switch (id) {
    case "wpm-distribution": {
      const m = mean(wpms),
        sd = Math.sqrt(mean(wpms.map((w) => (w - m) ** 2)));
      const best = maximum(wpms),
        worst = minimum(wpms);
      return [
        `Average speed: ${fmt(m)} WPM (standard deviation ${fmt(sd)} WPM).`,
        `Range: ${fmt(worst)}–${fmt(best)} WPM, a spread of ${fmt(best - worst)} WPM.`,
        `${fmt((100 * wpms.filter((w) => w >= m).length) / n)}% of races are at or above your average.`,
      ];
    }
    case "accuracy-distribution": {
      const m = mean(accs) * 100;
      const perfect = accs.filter((a) => a >= 0.99).length;
      return [
        `Average accuracy: ${fmt(m)}%.`,
        `${fmt((100 * perfect) / n)}% of races were at 99% accuracy or higher.`,
        `Accuracy ranges from ${fmt(minimum(accs) * 100)}% to ${fmt(maximum(accs) * 100)}%.`,
      ];
    }
    case "performance-over-time":
    case "daily-performance":
    case "hourly-performance": {
      const g =
        id === "performance-over-time"
          ? monthly(rows)
          : group(rows, (r) =>
              id === "daily-performance"
                ? r.d.slice(0, 10)
                : new Date(r.d).getUTCHours(),
            );
      if (g.length < 2)
        return n < 2
          ? []
          : [
              `All races fall in a single ${id === "hourly-performance" ? "hour" : "period"} (${g[0][0]}).`,
            ];
      const { lo, hi } = extremes(g, avg);
      const out = [
        `Highest average: ${fmt(hi![1])} WPM (${hi![0]}); lowest: ${fmt(lo![1])} WPM (${lo![0]}).`,
        `Difference between highest and lowest: ${fmt(hi![1] - lo![1])} WPM.`,
      ];
      if (id !== "hourly-performance") {
        const s = slope(g.map((x) => avg(x[1])));
        out.push(
          `Trend: ${s >= 0 ? "+" : ""}${fmt(s, 2)} WPM per period on average.`,
        );
      }
      return out;
    }
    case "rolling-average": {
      if (n < 100)
        return [`${n} races recorded; the rolling window needs 100.`];
      const roll: number[] = [];
      let s = 0;
      for (let i = 0; i < n; i++) {
        s += wpms[i];
        if (i >= 100) s -= wpms[i - 100];
        if (i >= 99) roll.push(s / 100);
      }
      const m = minimum(roll),
        x = maximum(roll);
      return [
        `Rolling average ranges from ${fmt(m)} to ${fmt(x)} WPM.`,
        `Latest rolling average: ${fmt(roll[roll.length - 1])} WPM vs overall ${fmt(mean(wpms))} WPM.`,
        `Change over the windowed span: ${fmt(roll[roll.length - 1] - roll[0])} WPM.`,
      ];
    }
    case "consistency-score": {
      if (n < 30)
        return [`${n} races recorded; 30 are needed for a standard deviation.`];
      const sds: number[] = [];
      for (let i = 29; i < n; i++) {
        const w = wpms.slice(i - 29, i + 1),
          m = mean(w);
        sds.push(Math.sqrt(w.reduce((sum, v) => sum + (v - m) ** 2, 0) / 29));
      }
      return [
        `Most recent 30-race standard deviation: ${fmt(sds[sds.length - 1])} WPM.`,
        `Lowest recorded: ${fmt(minimum(sds))} WPM; highest: ${fmt(maximum(sds))} WPM.`,
      ];
    }
    case "rank-distribution": {
      const wins = rows.filter((r) => r.r === 1).length;
      const g = group(rows, (r) => r.r);
      let top: [string, number] = [g[0][0], g[0][1].length];
      for (const [k, rs] of g) if (rs.length > top[1]) top = [k, rs.length];
      return [
        `Win rate: ${fmt((100 * wins) / n)}% (${wins.toLocaleString()} of ${n.toLocaleString()} races).`,
        `Most frequent rank: ${top[0]} (${fmt((100 * top[1]) / n)}% of races).`,
        `Average rank: ${fmt(mean(rows.map((r) => r.r)))} across ${g.length} distinct ranks.`,
      ];
    }
    case "accuracy-by-rank": {
      const g = group(rows, (r) => r.r);
      if (g.length < 2) return [];
      const { lo, hi } = extremes(g, (r) => mean(r.map((v) => v.a)));
      return [
        `Highest average accuracy: ${fmt(hi![1] * 100)}% at rank ${hi![0]}.`,
        `Lowest average accuracy: ${fmt(lo![1] * 100)}% at rank ${lo![0]}.`,
        `Gap between them: ${fmt((hi![1] - lo![1]) * 100)} percentage points.`,
      ];
    }
    case "wpm-vs-accuracy": {
      if (n < 2) return [];
      const mw = mean(wpms),
        ma = mean(accs);
      let num = 0,
        dw = 0,
        da = 0;
      for (let i = 0; i < n; i++) {
        num += (wpms[i] - mw) * (accs[i] - ma);
        dw += (wpms[i] - mw) ** 2;
        da += (accs[i] - ma) ** 2;
      }
      const r = dw && da ? num / Math.sqrt(dw * da) : 0;
      const sorted = [...wpms].sort((a, b) => a - b);
      const med =
        (sorted[Math.floor((n - 1) / 2)] + sorted[Math.floor(n / 2)]) / 2;
      const above = accs.filter((_, i) => wpms[i] > med);
      return [
        dw && da
          ? `Correlation between WPM and accuracy: ${fmt(r, 2)} (-1 to 1).`
          : "Correlation is undefined when speed or accuracy is constant.",
        above.length
          ? `Average accuracy above the median speed: ${fmt(mean(above) * 100)}%.`
          : "No races are above the median speed.",
      ];
    }
    case "win-rate-monthly": {
      const g = monthly(rows);
      if (g.length < 2) return [];
      const { lo, hi } = extremes(g, winRate);
      return [
        `Best month: ${hi![0]} at ${fmt(hi![1] * 100)}% wins.`,
        `Weakest month: ${lo![0]} at ${fmt(lo![1] * 100)}% wins.`,
        `Overall win rate: ${fmt(100 * winRate(rows))}%.`,
      ];
    }
    case "cumulative-accuracy": {
      const first = mean(accs.slice(0, Math.min(10, n))) * 100,
        last = mean(accs) * 100;
      return [
        `Cumulative average accuracy: ${fmt(last)}%.`,
        `First ${Math.min(10, n)} races averaged ${fmt(first)}%; a difference of ${fmt(last - first)} percentage points.`,
      ];
    }
    case "wpm-by-rank-boxplot": {
      const g = group(rows, (r) => r.r);
      if (g.length < 2) return [];
      const { lo, hi } = extremes(g, avg);
      return [
        `Highest average speed: rank ${hi![0]} averages ${fmt(hi![1])} WPM.`,
        `Rank ${lo![0]} averages ${fmt(lo![1])} WPM; ${fmt(hi![1] - lo![1])} WPM lower.`,
      ];
    }
    case "top-texts-distribution": {
      const g = frequent(rows, 10);
      const { lo, hi } = extremes(g, avg);
      return [
        `Among your ${g.length} most-played texts, ${hi![0]} averages ${fmt(hi![1])} WPM.`,
        `${lo![0]} averages ${fmt(lo![1])} WPM, ${fmt(hi![1] - lo![1])} WPM lower.`,
        `Most-played text: ${g[0][0]} with ${g[0][1].length} races.`,
      ];
    }
    case "racers-impact": {
      const g = group(rows, (r) => r.c);
      if (g.length < 2) return [];
      const { lo, hi } = extremes(g, avg);
      return [
        `Highest average: ${fmt(hi![1])} WPM in ${hi![0]}-racer races.`,
        `Lowest average: ${fmt(lo![1])} WPM in ${lo![0]}-racer races.`,
        `Field sizes range from ${g[0][0]} to ${g[g.length - 1][0]} racers.`,
      ];
    }
    case "top-texts": {
      const g = group(rows, (r) => r.t).filter((x) => x[1].length >= 5);
      if (!g.length) return [`No text has 5 or more races yet.`];
      const { lo, hi } = extremes(g, avg);
      return [
        `Best text: ${hi![0]} at ${fmt(hi![1])} WPM over ${hi && g.find((x) => x[0] === hi[0])![1].length} races.`,
        `Weakest text: ${lo![0]} at ${fmt(lo![1])} WPM; ${fmt(hi![1] - lo![1])} WPM apart.`,
      ];
    }
    case "frequent-texts-improvement": {
      const out: string[] = [];
      for (const [k, rs] of frequent(rows)) {
        if (rs.length < 3) continue;
        const ordered = [...rs].sort((a, b) => a.d.localeCompare(b.d));
        const half = Math.max(1, ordered.length >> 1);
        const d = avg(ordered.slice(-half)) - avg(ordered.slice(0, half));
        out.push(
          `Text ${k}: ${d >= 0 ? "+" : ""}${fmt(d)} WPM between the earliest and latest halves (${rs.length} races).`,
        );
      }
      return out.slice(0, 3);
    }
    case "win-rate-after-win": {
      if (n < 2) return [];
      let aw = 0,
        aww = 0,
        al = 0,
        alw = 0;
      for (let i = 1; i < n; i++) {
        if (rows[i - 1].r === 1) {
          aw++;
          if (rows[i].r === 1) aww++;
        } else {
          al++;
          if (rows[i].r === 1) alw++;
        }
      }
      if (!aw || !al) return [];
      return [
        `After a win: ${fmt((100 * aww) / aw)}% win rate (${aw} races).`,
        `After a non-win: ${fmt((100 * alw) / al)}% win rate (${al} races).`,
        `Difference: ${fmt(100 * (aww / aw - alw / al))} percentage points.`,
      ];
    }
    case "fastest-slowest-races": {
      const sorted = [...wpms].sort((a, b) => a - b);
      const k = Math.min(5, n);
      const slow = mean(sorted.slice(0, k)),
        fast = mean(sorted.slice(-k));
      return [
        `Average of ${k} fastest races: ${fmt(fast)} WPM.`,
        `Average of ${k} slowest races: ${fmt(slow)} WPM; a ${fmt(fast - slow)} WPM gap.`,
        `Fastest single race: ${fmt(sorted[n - 1])} WPM.`,
      ];
    }
    case "time-between-races": {
      const ordered = [...rows].sort((a, b) => a.d.localeCompare(b.d));
      const limits = [1, 3, 6, 12, 24, 48, 168, Infinity],
        labels = [
          "0–1h",
          "1–3h",
          "3–6h",
          "6–12h",
          "12–24h",
          "24–48h",
          "48h–1wk",
          "1wk+",
        ];
      const bins: Race[][] = limits.map(() => []);
      for (let i = 1; i < ordered.length; i++) {
        const h =
          (Date.parse(ordered[i].d) - Date.parse(ordered[i - 1].d)) / 3600000;
        bins[limits.findIndex((v) => h <= v)].push(ordered[i]);
      }
      const shown = bins
        .map((r, i) => [labels[i], r] as [string, Race[]])
        .filter((g) => g[1].length >= 5);
      if (shown.length < 2) return [];
      const { lo, hi } = extremes(shown, avg);
      return [
        `Best after ${hi![0]} breaks: ${fmt(hi![1])} WPM on average.`,
        `Lowest after ${lo![0]} breaks: ${fmt(lo![1])} WPM; ${fmt(hi![1] - lo![1])} WPM apart.`,
        `Groups with fewer than 5 races are excluded.`,
      ];
    }
    default:
      return [];
  }
}
