import type { Data, Layout, Config } from "plotly.js";
export interface StatsResponse {
  total_races: number;
  avg_wpm: number;
  best_wpm: number;
  total_wins: number;
  avg_accuracy: number;
  date_range: { start: string; end: string };
}
export interface ChartResponse {
  data: Data[];
  layout: Partial<Layout>;
  insights: string[];
  has_insights: boolean;
}
export interface RaceData {
  stats: StatsResponse;
  csvData: string;
}
export type ChartData = ChartResponse & { config?: Partial<Config> };
