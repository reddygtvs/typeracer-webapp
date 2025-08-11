import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

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

export const getStats = async (csvData: string): Promise<StatsResponse> => {
  const response = await api.post('/stats', { csv_data: csvData });
  return response.data;
};

export const getChart = async (chartType: string, csvData: string): Promise<ChartResponse> => {
  const response = await api.post(`/charts/${chartType}`, { csv_data: csvData });
  return response.data;
};

// Remove these functions completely:
// export const uploadData = async (file: File) => { ... }
// export const useSampleData = async () => { ... }