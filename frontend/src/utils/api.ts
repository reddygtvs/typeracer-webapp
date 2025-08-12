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

// Batch multiple chart requests for better performance
export const getChartsBatch = async (chartTypes: string[], csvData: string): Promise<Record<string, ChartResponse>> => {
  // Execute all chart requests in parallel
  const promises = chartTypes.map(async (chartType) => {
    try {
      const result = await getChart(chartType, csvData);
      return { chartType, result, error: null };
    } catch (error) {
      return { chartType, result: null, error };
    }
  });
  
  const results = await Promise.allSettled(promises);
  const chartData: Record<string, ChartResponse> = {};
  
  results.forEach((result, index) => {
    if (result.status === 'fulfilled' && result.value.result) {
      chartData[chartTypes[index]] = result.value.result;
    }
  });
  
  return chartData;
};

// Utility for client-side caching of chart results
const chartCache = new Map<string, { data: ChartResponse; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

export const getCachedChart = (chartType: string, csvData: string): ChartResponse | null => {
  const cacheKey = `${chartType}_${csvData.slice(0, 100)}`; // Use first 100 chars as key
  const cached = chartCache.get(cacheKey);
  
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data;
  }
  
  return null;
};

export const setCachedChart = (chartType: string, csvData: string, data: ChartResponse): void => {
  const cacheKey = `${chartType}_${csvData.slice(0, 100)}`;
  chartCache.set(cacheKey, { data, timestamp: Date.now() });
  
  // Clean old entries
  if (chartCache.size > 100) {
    const oldest = Array.from(chartCache.entries())
      .sort((a, b) => a[1].timestamp - b[1].timestamp)[0];
    chartCache.delete(oldest[0]);
  }
};