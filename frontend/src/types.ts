// Add these new interfaces
export interface StatsResponse {
  total_races: number;
  avg_wpm: number;
  best_wpm: number;
  total_wins: number;
  avg_accuracy: number;
  date_range: {
    start: string;
    end: string;
  };
}

export interface ChartResponse {
  data: any[];
  layout: any;
  insights: string[];
  has_insights: boolean;
}

// Update the existing RaceData interface
export interface RaceData {
  stats: StatsResponse;
  csvData: string; // ADD this field
}

// Keep existing ChartData interface as is
export type ChartData = {
  data: any[];
  layout: any;
  config?: any;
  insights?: string[];
  has_insights?: boolean;
};