import { test } from "node:test";
import assert from "node:assert/strict";
import { parseCSV, chart } from "../src/utils/analytics.ts";
const header = "Race #,WPM,Accuracy,Rank,# Racers,Text ID,Date/Time (UTC)\n";
const csv =
  header +
  Array.from(
    { length: 120 },
    (_, i) =>
      `${i + 1},${60 + (i % 40)},0.9${i % 10},${(i % 3) + 1},${((i % 3) + 1) + (i % 4)},${(i % 6) + 1},2026-09-${String((i % 28) + 1).padStart(2, "0")} ${String(i % 24).padStart(2, "0")}:${String(i % 60).padStart(2, "0")}:00`,
  ).join("\n");
const rows = parseCSV(csv);
const line = (id: string) =>
  chart(id, rows).data[0] as { line?: { color: string }; marker: unknown };
test("per-chart line colors match original Python charts", () => {
  assert.equal(line("performance-over-time").line?.color, "#10b981");
  assert.equal(line("daily-performance").line?.color, "#f97316");
  assert.equal(line("rolling-average").line?.color, "#8b5cf6");
  assert.equal(line("consistency-score").line?.color, "#f97316");
  assert.equal(line("cumulative-accuracy").line?.color, "#8b5cf6");
  assert.equal(line("racers-impact").line?.color, "#14b8a6");
});
test("histogram colors: WPM green, accuracy red", () => {
  const wpm = chart("wpm-distribution", rows).data[0] as {
    marker: { color: string };
  };
  const acc = chart("accuracy-distribution", rows).data[0] as {
    marker: { color: string };
  };
  assert.equal(wpm.marker.color, "#39FF14");
  assert.equal(acc.marker.color, "#ef4444");
});
test("continuous colorscale bars with colorbars", () => {
  const cases: [string, string, string][] = [
    ["rank-distribution", "Viridis", "%"],
    ["hourly-performance", "Blues", ""],
    ["top-texts", "Viridis", ""],
    ["accuracy-by-rank", "RdYlGn", "%"],
    ["win-rate-after-win", "Viridis", "%"],
    ["time-between-races", "RdYlGn", ""],
  ];
  for (const [id, scale, unit] of cases) {
    const m = (
      chart(id, rows).data[0] as {
        marker: {
          color: number[];
          colorscale: string;
          showscale: boolean;
          colorbar: { ticksuffix: string };
        };
      }
    ).marker;
    assert.equal(m.colorscale, scale, id);
    assert.equal(m.showscale, true, id);
    assert.equal(m.colorbar.ticksuffix, unit, id);
    assert.ok(Array.isArray(m.color), id);
  }
});
test("colorbar uses real percent units for percent charts", () => {
  const m = (
    chart("rank-distribution", rows).data[0] as {
      marker: { color: number[] };
      y: number[];
    }
  ).marker;
  const total = m.color.reduce((a, b) => a + b, 0);
  assert.ok(Math.abs(total - 100) < 1e-9);
});
test("scatter and multi-series colors match originals", () => {
  const scatter = chart("wpm-vs-accuracy", rows).data[0] as {
    marker: { color: string };
  };
  assert.equal(scatter.marker.color, "#636efa");
  const monthly = chart("win-rate-monthly", rows).data[0] as {
    marker: { color: string };
  };
  assert.equal(monthly.marker.color, "#eab308");
  const fs = chart("fastest-slowest-races", rows).data as {
    marker: { color: string };
  }[];
  assert.deepEqual(
    fs.map((t) => t.marker.color),
    ["blue", "red"],
  );
  const texts = chart("frequent-texts-improvement", rows).data as {
    line: { color: string };
  }[];
  const expected = ["#39FF14", "#FF6B6B", "#74B9FF", "#A29BFE", "#FD79A8"];
  texts.forEach((t, i) => assert.equal(t.line.color, expected[i]));
  const boxes = chart("top-texts-distribution", rows).data as {
    marker: { color: string };
  }[];
  assert.ok(new Set(boxes.map((b) => b.marker.color)).size > 1);
  const rankBoxes = chart("wpm-by-rank-boxplot", rows).data as {
    marker: { color: string };
  }[];
  rankBoxes.forEach((b) => assert.equal(b.marker.color, "#636efa"));
});
