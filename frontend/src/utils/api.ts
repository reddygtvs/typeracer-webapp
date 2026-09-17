import type { StatsResponse, ChartResponse } from "../types";
let worker: Worker | undefined;
let sequence = 0;
let currentCSV: string | undefined;
const pending = new Map<
  number,
  { resolve: (v: unknown) => void; reject: (e: Error) => void }
>();
function request(
  kind: string,
  csv: string,
  chartType?: string,
): Promise<unknown> {
  if (!worker) {
    worker = new Worker(new URL("./analytics.worker.ts", import.meta.url), {
      type: "module",
    });
    worker.onmessage = ({ data }) => {
      const p = pending.get(data.id);
      if (!p) return;
      pending.delete(data.id);
      if (data.error) {
        currentCSV = undefined;
        p.reject(new Error(data.error));
      } else p.resolve(data.result);
    };
    worker.onerror = () => {
      for (const p of pending.values())
        p.reject(new Error("Analysis worker failed. Please reload."));
      pending.clear();
      worker?.terminate();
      worker = undefined;
      currentCSV = undefined;
    };
  }
  return new Promise((resolve, reject) => {
    const id = ++sequence;
    pending.set(id, { resolve, reject });
    const nextCSV = currentCSV === csv ? undefined : csv;
    currentCSV = csv;
    worker!.postMessage({ id, kind, csv: nextCSV, chartType });
  });
}
export const getStats = (csv: string): Promise<StatsResponse> =>
  request("stats", csv) as Promise<StatsResponse>;
export const getChart = (
  chartType: string,
  csv: string,
): Promise<ChartResponse> =>
  request("chart", csv, chartType) as Promise<ChartResponse>;
