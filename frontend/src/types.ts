export type RaceData = {
  stats: {
    total_races: number;
    avg_wpm: number;
    best_wpm: number;
    total_wins: number;
    avg_accuracy: number;
    date_range: {
      start: string;
      end: string;
    };
  };
};

export type ChartData = {
  data: any[];
  layout: any;
  config?: any;
};