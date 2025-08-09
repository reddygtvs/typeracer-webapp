import React from 'react';
import Plot from 'react-plotly.js';
import { getChart } from '../utils/api';
import { ChartData } from '../types';
import { BarChart3, LineChart, PieChart, Clock, TrendingUp } from 'lucide-react';

const chartConfigs = [
  {
    id: 'wpm-distribution',
    title: 'WPM Distribution',
    description: 'Distribution of your typing speeds',
    icon: BarChart3,
  },
  {
    id: 'accuracy-distribution',
    title: 'Accuracy Distribution',
    description: 'Distribution of your accuracy scores',
    icon: BarChart3,
  },
  {
    id: 'performance-over-time',
    title: 'Performance Over Time',
    description: 'Monthly average WPM trends',
    icon: LineChart,
  },
  {
    id: 'daily-performance',
    title: 'Daily Performance',
    description: 'Daily average WPM over time',
    icon: LineChart,
  },
  {
    id: 'rolling-average',
    title: 'Rolling Average',
    description: '100-race rolling average WPM',
    icon: TrendingUp,
  },
  {
    id: 'rank-distribution',
    title: 'Rank Distribution',
    description: 'How often you place in each rank',
    icon: PieChart,
  },
  {
    id: 'hourly-performance',
    title: 'Performance by Hour',
    description: 'Your best typing times of day',
    icon: Clock,
  },
  {
    id: 'wpm-vs-accuracy',
    title: 'WPM vs Accuracy',
    description: 'Relationship between speed and accuracy',
    icon: LineChart,
  },
  {
    id: 'win-rate-monthly',
    title: 'Monthly Win Rate',
    description: 'Win rate trends over time',
    icon: TrendingUp,
  },
  {
    id: 'top-texts',
    title: 'Top vs Bottom Texts',
    description: 'Best and worst performing texts',
    icon: BarChart3,
  },
  {
    id: 'consistency-score',
    title: 'Consistency Score',
    description: 'Performance consistency over time',
    icon: LineChart,
  },
  {
    id: 'accuracy-by-rank',
    title: 'Accuracy by Rank',
    description: 'Average accuracy for each rank position',
    icon: BarChart3,
  },
  {
    id: 'cumulative-accuracy',
    title: 'Cumulative Accuracy',
    description: 'Average accuracy improvement over time',
    icon: TrendingUp,
  },
  {
    id: 'wpm-by-rank-boxplot',
    title: 'WPM Distribution by Rank',
    description: 'Box plot showing WPM outliers by rank',
    icon: BarChart3,
  },
  {
    id: 'racers-impact',
    title: 'Number of Racers Impact',
    description: 'How competition level affects performance',
    icon: LineChart,
  },
  {
    id: 'frequent-texts-improvement',
    title: 'Frequent Texts Improvement',
    description: 'WPM improvement over time for most frequent texts',
    icon: TrendingUp,
  },
  {
    id: 'top-texts-distribution',
    title: 'Top Texts WPM Distribution',
    description: 'WPM distribution for most frequent texts',
    icon: BarChart3,
  },
  {
    id: 'win-rate-after-win',
    title: 'Win Rate After Previous Win',
    description: 'Performance momentum analysis',
    icon: BarChart3,
  },
  {
    id: 'fastest-slowest-races',
    title: 'Fastest vs Slowest Races',
    description: 'Highlighting your best and worst performances',
    icon: TrendingUp,
  },
  {
    id: 'time-between-races',
    title: 'Time Between Races Impact',
    description: 'How rest time affects performance',
    icon: Clock,
  },
];

// Independent ChartCard component with its own state
const ChartCard: React.FC<{ config: typeof chartConfigs[0]; autoLoad?: boolean }> = ({ 
  config, 
  autoLoad = false 
}) => {
  const [chartData, setChartData] = React.useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string>('');
  const Icon = config.icon;

  const loadChart = async () => {
    if (isLoading || chartData) return;

    setIsLoading(true);
    setError('');
    
    try {
      const data = await getChart(config.id);
      setChartData(data);
    } catch (error: any) {
      setError(error.response?.data?.detail || 'Failed to load chart');
    } finally {
      setIsLoading(false);
    }
  };

  React.useEffect(() => {
    if (autoLoad) {
      loadChart();
    }
  }, [autoLoad]);

    return (
      <div className="bg-bg-primary rounded-lg border border-border-default overflow-hidden hover:border-border-hover transition-all duration-200">
        <div className="px-6 py-4 bg-hover-bg border-b border-border-default">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-bg-primary border border-border-default rounded-lg">
              <Icon className="h-5 w-5 text-spotify" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-text-primary text-glow-white">{config.title}</h3>
              <p className="text-sm text-text-secondary">{config.description}</p>
            </div>
          </div>
        </div>
        
        <div className="p-6">
          {/* Fixed height container to prevent layout shift */}
          <div className="h-[400px] flex items-center justify-center">
            {!chartData && !isLoading && !error && (
              <button
                onClick={loadChart}
                className="px-4 py-2 bg-transparent border border-border-default text-text-secondary rounded-lg hover:bg-hover-bg hover:border-border-hover hover:text-text-accent transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-spotify focus:ring-offset-2 focus:ring-offset-black"
              >
                Load Chart
              </button>
            )}
            
            {isLoading && (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-spotify"></div>
                <p className="mt-4 text-sm text-text-secondary">Loading chart...</p>
              </div>
            )}
            
            {error && (
              <div className="flex flex-col items-center">
                <p className="text-red-400 text-sm">{error}</p>
                <button
                  onClick={loadChart}
                  className="mt-2 px-4 py-2 bg-red-900/20 border border-red-700/30 text-red-300 rounded-lg hover:bg-red-800/20 hover:border-red-600/50 transition-all duration-200"
                >
                  Retry
                </button>
              </div>
            )}
            
            {chartData && (
              <Plot
                data={chartData.data}
                layout={{
                  ...chartData.layout,
                  autosize: true,
                  margin: { l: 50, r: 50, t: 50, b: 50 },
                  paper_bgcolor: 'rgba(0,0,0,0)',
                  plot_bgcolor: 'rgba(0,0,0,0)',
                  font: {
                    color: 'rgb(255, 255, 255)',
                    family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif'
                  },
                  xaxis: {
                    ...chartData.layout.xaxis,
                    color: 'rgb(181, 179, 173)',
                    gridcolor: 'rgb(55, 55, 53)',
                    zerolinecolor: 'rgb(55, 55, 53)'
                  },
                  yaxis: {
                    ...chartData.layout.yaxis,
                    color: 'rgb(181, 179, 173)',
                    gridcolor: 'rgb(55, 55, 53)',
                    zerolinecolor: 'rgb(55, 55, 53)'
                  }
                }}
                style={{ width: '100%', height: '400px' }}
                config={{ 
                  displayModeBar: false,
                  responsive: true,
                }}
              />
            )}
          </div>
        </div>
      </div>
    );
};

const ChartGrid: React.FC = () => {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {chartConfigs.map((config, index) => (
        <ChartCard 
          key={config.id} 
          config={config} 
          autoLoad={index < 2} // Auto-load first 2 charts
        />
      ))}
    </div>
  );
};

export default ChartGrid;