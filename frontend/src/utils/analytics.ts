import type { Layout } from "plotly.js";
import { calculateInsights } from "./insights";
import Papa from "papaparse";
type Trace = {
  x?: (string | number)[];
  y: (number | null)[];
  type: string;
  [key: string]: unknown;
};
export type Race = {
  n: number;
  w: number;
  a: number;
  r: number;
  c: number;
  t: string;
  d: string;
};
export function parseCSV(csv: string): Race[] {
  if (csv.length > 20_000_000) throw Error("CSV exceeds the 20 MB limit.");
  const p = Papa.parse<Record<string, string>>(csv.trim(), {
    header: true,
    skipEmptyLines: "greedy",
    transformHeader: (h) => h.trim().replace(/^\uFEFF/, ""),
  });
  const required = [
    "Race #",
    "WPM",
    "Accuracy",
    "Rank",
    "# Racers",
    "Text ID",
    "Date/Time (UTC)",
  ];
  if (p.errors.length || required.some((k) => !p.meta.fields?.includes(k)))
    throw Error("Invalid CSV. Use the TypeRacer export column format.");
  const rows = p.data.map((v, i) => {
    const num = (k: string) => (v[k]?.trim() ? Number(v[k]) : NaN);
    const raw = v.Accuracy?.trim() || "";
    const a = raw.endsWith("%")
      ? Number(raw.slice(0, -1)) / 100
      : num("Accuracy");
    const d = v["Date/Time (UTC)"];
    const iso = d?.replace(" ", "T") + "Z";
    const row = {
      n: num("Race #"),
      w: num("WPM"),
      a,
      r: num("Rank"),
      c: num("# Racers"),
      t: v["Text ID"],
      d: iso,
    };
    if (
      ![row.n, row.w, a, row.r, row.c].every(Number.isFinite) ||
      a < 0 ||
      a > 1 ||
      row.w <= 0 ||
      !Number.isInteger(row.n) ||
      row.n < 1 ||
      !Number.isInteger(row.r) ||
      row.r < 1 ||
      !Number.isInteger(row.c) ||
      row.c < row.r ||
      !row.t ||
      !/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$/.test(d) ||
      !Number.isFinite(Date.parse(iso)) ||
      new Date(iso).toISOString().slice(0, 19) + "Z" !== iso
    )
      throw Error(
        `Invalid race data on row ${i + 2}. Accuracy must be 0 to 1 or include %. Dates must use UTC.`,
      );
    return row;
  });
  if (!rows.length) throw Error("The CSV contains no races.");
  return rows.sort((a, b) => a.n - b.n);
}
const mean = (v: number[]) =>
  v.length ? v.reduce((a, b) => a + b, 0) / v.length : 0;
function group(rows: Race[], key: (r: Race) => string | number) {
  const m = new Map<string, Race[]>();
  for (const r of rows) {
    const k = String(key(r));
    if (!m.has(k)) m.set(k, []);
    m.get(k)!.push(r);
  }
  return [...m].sort((a, b) =>
    a[0].localeCompare(b[0], undefined, { numeric: true }),
  );
}
export function stats(rows: Race[]) {
  const dates = rows.map((r) => r.d).sort();
  return {
    total_races: rows.length,
    avg_wpm: mean(rows.map((r) => r.w)),
    best_wpm: rows.reduce((m, r) => Math.max(m, r.w), 0),
    total_wins: rows.filter((r) => r.r === 1).length,
    avg_accuracy: mean(rows.map((r) => r.a)),
    date_range: { start: dates[0], end: dates[dates.length - 1] },
  };
}
export function chart(id: string, rows: Race[]) {
  const data: Trace[] = [];
  let title = "",
    xTitle = "",
    yTitle = "WPM";
  const layout: Partial<Layout> = { showlegend: false };
  const insights: string[] = [];
  const trace = (
    x: (string | number)[],
    y: (number | null)[],
    type = "scatter",
    name = "",
  ) => ({
    x,
    y,
    type,
    mode: "lines",
    name,
    line: { color: "#39FF14", width: 2 },
    marker: { color: "#39FF14" },
  });
  const bars = (groups: [string, Race[]][], value: (r: Race[]) => number) => {
    data.push(
      trace(
        groups.map((g) => g[0]),
        groups.map((g) => value(g[1])),
        "bar",
      ),
    );
  };
  const avg = (r: Race[]) => mean(r.map((v) => v.w));
  const monthly = () => group(rows, (r) => r.d.slice(0, 7));
  const rolling = (rs: Race[], size: number, partial = false) => {
    let sum = 0;
    return rs.map((r, i) => {
      sum += r.w;
      if (i >= size) sum -= rs[i - size].w;
      return i + 1 < size && !partial ? null : sum / Math.min(i + 1, size);
    });
  };
  const frequent = (limit = 5) =>
    group(rows, (r) => r.t)
      .sort((a, b) => b[1].length - a[1].length)
      .slice(0, limit);
  switch (id) {
    case "wpm-distribution":
    case "accuracy-distribution": {
      const acc = id === "accuracy-distribution";
      const values = rows.map((r) => (acc ? r.a * 100 : r.w));
      title = acc ? "Accuracy Distribution" : "WPM Distribution";
      xTitle = acc ? "Accuracy (%)" : "WPM";
      yTitle = "Races";
      const lo = values.reduce((m, v) => Math.min(m, v), Infinity),
        hi = values.reduce((m, v) => Math.max(m, v), -Infinity),
        step = (hi - lo) / (acc ? 30 : 15) || 1;
      const bins = Array(acc ? 30 : 15).fill(0);
      for (const v of values)
        bins[Math.min(bins.length - 1, Math.floor((v - lo) / step))]++;
      data.push(
        trace(
          bins.map((_, i) => lo + (i + 0.5) * step),
          bins,
          "bar",
        ),
      );
      insights.push(
        `Mean: ${mean(values).toFixed(1)}${acc ? "%" : " WPM"}`,
        `${rows.length.toLocaleString()} races`,
      );
      break;
    }
    case "performance-over-time":
    case "daily-performance":
    case "hourly-performance": {
      const groups =
        id === "performance-over-time"
          ? monthly()
          : group(rows, (r) =>
              id === "daily-performance"
                ? r.d.slice(0, 10)
                : new Date(r.d).getUTCHours(),
            );
      title =
        id === "hourly-performance"
          ? "Average WPM by Hour (UTC)"
          : "Average WPM Over Time";
      xTitle = id === "hourly-performance" ? "Hour (UTC)" : "Date";
      data.push(
        trace(
          groups.map((g) => g[0]),
          groups.map((g) => avg(g[1])),
          id === "hourly-performance" ? "bar" : "scatter",
        ),
      );
      break;
    }
    case "rolling-average":
      title = "100-Race Rolling Average";
      xTitle = "Race Number";
      data.push(
        trace(
          rows.map((r) => r.n),
          rolling(rows, 100),
        ),
      );
      if (rows.length < 100) insights.push("At least 100 races are required.");
      break;
    case "consistency-score":
      title = "30-Race Standard Deviation";
      xTitle = "Race Number";
      yTitle = "WPM standard deviation";
      data.push(
        trace(
          rows.map((r) => r.n),
          rows.map((_, i) => {
            if (i < 29) return null;
            const v = rows.slice(i - 29, i + 1).map((r) => r.w),
              m = mean(v);
            return Math.sqrt(v.reduce((s, w) => s + (w - m) ** 2, 0) / 29);
          }),
        ),
      );
      insights.push("Lower values show more consistent speed.");
      break;
    case "rank-distribution":
      title = "Rank Distribution";
      xTitle = "Rank";
      yTitle = "Races (%)";
      bars(
        group(rows, (r) => r.r),
        (r) => (100 * r.length) / rows.length,
      );
      break;
    case "accuracy-by-rank":
      title = "Average Accuracy by Rank";
      xTitle = "Rank";
      yTitle = "Average Accuracy (%)";
      bars(
        group(rows, (r) => r.r),
        (r) => mean(r.map((v) => v.a)) * 100,
      );
      data[0].text = data[0].y.map((v) => `${Number(v).toFixed(1)}%`);
      data[0].texttemplate = "%{text}";
      data[0].textposition = "outside";
      data[0].cliponaxis = false;
      layout.yaxis = { range: [0, 105], ticksuffix: "%" };
      data[0].hovertemplate = "Rank %{x}<br>%{y:.1f}%<extra></extra>";
      break;
    case "wpm-vs-accuracy":
      title = "Speed and Accuracy";
      xTitle = "WPM";
      yTitle = "Accuracy (%)";
      data.push({
        ...trace(
          rows.map((r) => r.w),
          rows.map((r) => r.a * 100),
        ),
        mode: "markers",
        marker: { color: "#39FF14", size: 3, opacity: 0.35 },
      });
      break;
    case "win-rate-monthly":
      title = "Monthly Win Rate";
      xTitle = "Month";
      yTitle = "Win Rate (%)";
      bars(
        monthly(),
        (r) => (100 * r.filter((v) => v.r === 1).length) / r.length,
      );
      break;
    case "cumulative-accuracy": {
      title = "Cumulative Average Accuracy";
      xTitle = "Race Number";
      yTitle = "Accuracy (%)";
      let sum = 0;
      data.push(
        trace(
          rows.map((r) => r.n),
          rows.map((r, i) => ((sum += r.a) * 100) / (i + 1)),
        ),
      );
      break;
    }
    case "wpm-by-rank-boxplot":
    case "top-texts-distribution": {
      title =
        id === "wpm-by-rank-boxplot"
          ? "WPM Distribution by Rank"
          : "WPM for Top 10 Texts";
      xTitle = id === "wpm-by-rank-boxplot" ? "Rank" : "Text ID";
      const groups =
        id === "wpm-by-rank-boxplot" ? group(rows, (r) => r.r) : frequent(10);
      for (const [key, rs] of groups)
        data.push({
          type: "box",
          name: key,
          y: rs.map((r) => r.w),
          boxpoints: "outliers",
          marker: { color: "#39FF14" },
        });
      break;
    }
    case "racers-impact": {
      title = "Performance by Number of Racers";
      xTitle = "Racers";
      const groups = group(rows, (r) => r.c);
      data.push(
        trace(
          groups.map((g) => g[0]),
          groups.map((g) => avg(g[1])),
        ),
      );
      break;
    }
    case "top-texts": {
      title = "Best and Worst Texts (5+ Races)";
      xTitle = "Text ID";
      const groups = group(rows, (r) => r.t)
        .filter((g) => g[1].length >= 5)
        .sort((a, b) => avg(b[1]) - avg(a[1]));
      const selected = [
        ...new Map([...groups.slice(0, 10), ...groups.slice(-10)]).entries(),
      ];
      bars(selected, avg);
      layout.xaxis = { type: "category" };
      if (!selected.length)
        insights.push("At least five races on one text are required.");
      break;
    }
    case "frequent-texts-improvement":
      title = "Top 5 Texts: 10-Race Average";
      xTitle = "Date";
      for (const [key, rs] of frequent()) {
        const ordered = [...rs].sort((a, b) => a.d.localeCompare(b.d));
        if (rs.length >= 3)
          data.push({
            ...trace(
              ordered.map((r) => r.d),
              rolling(ordered, 10, true),
              "scatter",
              key,
            ),
            line: { width: 2 },
          });
      }
      layout.showlegend = true;
      break;
    case "win-rate-after-win": {
      title = "Win Rate After Previous Result";
      xTitle = "Previous Result";
      yTitle = "Win Rate (%)";
      const groups = new Map<string, Race[]>();
      for (let i = 1; i < rows.length; i++) {
        const k = rows[i - 1].r === 1 ? "Win" : "Loss";
        const a = groups.get(k);
        if (a) a.push(rows[i]);
        else groups.set(k, [rows[i]]);
      }
      bars(
        [...groups].sort((a, b) => a[0].localeCompare(b[0])),
        (r) => (100 * r.filter((v) => v.r === 1).length) / r.length,
      );
      insights.push(
        "The first race is excluded because it has no previous result.",
      );
      break;
    }
    case "fastest-slowest-races": {
      title = "Five Fastest and Slowest Races";
      xTitle = "Race Number";
      const sorted = [...rows].sort((a, b) => a.w - b.w);
      for (const [name, rs] of [
        ["Slowest", sorted.slice(0, 5)],
        ["Fastest", sorted.slice(-5)],
      ] as [string, Race[]][])
        data.push({
          ...trace(
            rs.map((r) => r.n),
            rs.map((r) => r.w),
            "scatter",
            name,
          ),
          mode: "markers",
          marker: {
            color: name === "Fastest" ? "#39FF14" : "#ff6b6b",
            size: 9,
          },
        });
      layout.showlegend = true;
      break;
    }
    case "time-between-races": {
      title = "WPM by Time Between Races";
      xTitle = "Break";
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
        const hours =
          (Date.parse(ordered[i].d) - Date.parse(ordered[i - 1].d)) / 3600000;
        bins[limits.findIndex((v) => hours <= v)].push(ordered[i]);
      }
      bars(
        bins
          .map((r, i) => [labels[i], r] as [string, Race[]])
          .filter((g) => g[1].length >= 5),
        avg,
      );
      insights.push("Each displayed group has at least five races.");
      break;
    }
    default:
      throw Error("Unknown chart");
  }
  insights.push(...calculateInsights(id, rows));
  if (!insights.length)
    insights.push(
      `${rows.length.toLocaleString()} races in this dataset.`,
      "Times use UTC. Hover over the chart for values.",
    );
  return {
    data,
    layout: {
      title: { text: title, font: { size: 14 } },
      xaxis: { title: { text: xTitle }, ...layout.xaxis },
      yaxis: { title: { text: yTitle }, ...layout.yaxis },
      ...Object.fromEntries(
        Object.entries(layout).filter(([k]) => k !== "xaxis" && k !== "yaxis"),
      ),
    },
    insights,
    has_insights: true,
  };
}
