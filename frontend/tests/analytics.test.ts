import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { parseCSV, stats, chart } from "../src/utils/analytics.ts";
const header = "Race #,WPM,Accuracy,Rank,# Racers,Text ID,Date/Time (UTC)\n";
const csv =
  header +
  "1,80,0.98,1,3,10,2026-09-01 12:00:00\n2,100,0.96,2,3,10,2026-09-01 12:01:00";
const rows = parseCSV(csv);
const sample = parseCSV(
  readFileSync(new URL("../public/sample-data.csv", import.meta.url), "utf8"),
);
const ref = JSON.parse(
  readFileSync(
    new URL("../../metrics/sample-reference.json", import.meta.url),
    "utf8",
  ),
);
test("sample statistics match independent Python reference", () => {
  const result = stats(sample);
  for (const k of Object.keys(ref))
    assert.ok(
      Math.abs((result[k as keyof typeof result] as number) - ref[k]) < 1e-9,
      k,
    );
});
test("accuracy by rank uses 0 to 100 values and percent labels", () => {
  const c = chart("accuracy-by-rank", rows);
  assert.deepEqual(c.data[0].y, [98, 96]);
  assert.deepEqual(c.data[0].text, ["98.0%", "96.0%"]);
});
test("explicit percent and CSV BOM/CRLF are accepted", () => {
  const r = parseCSV(
    "\uFEFF" + csv.replace("0.98", "98%").replaceAll("\n", "\r\n"),
  );
  assert.equal(r[0].a, 0.98);
});
test("invalid accuracy, missing headers, blank data and impossible dates are rejected", () => {
  for (const v of [
    "",
    header,
    "wrong\n1",
    csv.replace("0.98", "98"),
    csv.replace("2026-09-01", "2026-02-30"),
    csv.replace(",80,", ",NaN,"),
  ])
    assert.throws(() => parseCSV(v));
});
test("previous result excludes first race and absent previous categories", () => {
  const c = chart("win-rate-after-win", rows);
  assert.deepEqual(c.data[0].x, ["Win"]);
  assert.deepEqual(c.data[0].y, [0]);
  const single = chart("win-rate-after-win", [rows[0]]);
  assert.equal(single.data[0].y.length, 0);
});
test("100-race moving average and sample standard deviation", () => {
  const r = Array.from({ length: 101 }, (_, i) => ({
    ...rows[0],
    n: i + 1,
    w: i + 1,
  }));
  const avg = chart("rolling-average", r).data[0].y;
  assert.equal(avg[98], null);
  assert.equal(avg[99], 50.5);
  assert.equal(avg[100], 51.5);
  const sd = chart("consistency-score", r).data[0].y;
  assert.equal(sd[28], null);
  assert.ok(Math.abs(sd[29] - Math.sqrt(77.5)) < 1e-9);
});
const source = readFileSync(
  new URL("../src/components/ChartGrid.tsx", import.meta.url),
  "utf8",
);
const ids = [...source.matchAll(/id: ["']([^"']+)["']/g)].map((m) => m[1]);
test("all 20 charts support sample data and a single race without invalid numeric values", () => {
  assert.equal(ids.length, 20);
  const inspect = (x: unknown) => {
    if (typeof x === "string") assert.ok(!/NaN|Infinity/.test(x), x);
    else if (typeof x === "number") assert.ok(Number.isFinite(x));
    else if (Array.isArray(x)) x.forEach(inspect);
    else if (x && typeof x === "object") Object.values(x).forEach(inspect);
  };
  for (const id of ids) {
    inspect(chart(id, sample));
    inspect(chart(id, [rows[0]]));
  }
});
test("histogram includes all races, including maximum value", () => {
  for (const id of ["wpm-distribution", "accuracy-distribution"])
    assert.equal(
      chart(id, sample).data[0].y.reduce((a: number, b: number) => a + b, 0),
      sample.length,
    );
});
test("large arrays do not overflow argument limits", () => {
  const r = Array.from({ length: 150000 }, (_, i) => ({
    ...rows[0],
    n: i + 1,
  }));
  assert.equal(
    chart("wpm-distribution", r).data[0].y.reduce(
      (a: number, b: number) => a + b,
      0,
    ),
    r.length,
  );
  chart("win-rate-after-win", r);
});
