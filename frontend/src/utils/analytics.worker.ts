import { parseCSV, stats, chart } from "./analytics";
import type { Race } from "./analytics";
let currentCSV = "";
let rows: Race[] = [];
self.onmessage = ({ data: { id, kind, csv, chartType } }) => {
  try {
    if (csv !== undefined && csv !== currentCSV) {
      rows = parseCSV(csv);
      currentCSV = csv;
    }
    const result = kind === "stats" ? stats(rows) : chart(chartType, rows);
    self.postMessage({ id, result });
  } catch (e) {
    currentCSV = "";
    rows = [];
    self.postMessage({
      id,
      error: e instanceof Error ? e.message : "Could not process the CSV.",
    });
  }
};
