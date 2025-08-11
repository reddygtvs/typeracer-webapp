import React from 'react';
import Plot from 'react-plotly.js';
import { getChart } from '../utils/api';
import { ChartData } from '../types';
import { BarChart3, LineChart, PieChart, Clock, TrendingUp } from 'lucide-react';
import ChartInsights from './ChartInsights';

const useWindowSize = () => {
  const [windowSize, setWindowSize] = React.useState({
    width: typeof window !== 'undefined' ? window.innerWidth : 1024,
  });

  React.useEffect(() => {
    if (typeof window === 'undefined') return;

    const handleResize = () => {
      setWindowSize({
        width: window.innerWidth,
      });
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return windowSize;
};

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
const ChartCard: React.FC<{
  config: typeof chartConfigs[0];
  csvData: string;
  autoLoad?: boolean
}> = ({ config, csvData, autoLoad = false }) => {
  const [chartData, setChartData] = React.useState<ChartData | null>(null);
  const [isLoading, setIsLoading] = React.useState(false);
  const [error, setError] = React.useState<string>('');
  const [hasTriggeredLoad, setHasTriggeredLoad] = React.useState(false);
  const { width } = useWindowSize();
  const chartRef = React.useRef<HTMLDivElement>(null);
  const Icon = config.icon;
  
  // Mock insights for now - will be replaced with real data from API
  const mockInsights = {
    insights: [
      "Insufficient data for detailed analysis",
      `Showing data for ${config.title}`,
      "Upload more data for insights"
    ],
    has_insights: false
  };

  const loadChart = async () => {
    if (isLoading || chartData) return;

    setIsLoading(true);
    setError('');
    
    try {
      const data = await getChart(config.id, csvData);
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
      setHasTriggeredLoad(true);
      return;
    }

    // Don't observe if already triggered or if chart is already loaded
    if (hasTriggeredLoad || chartData) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const [entry] = entries;
        if (entry.isIntersecting && !hasTriggeredLoad && !chartData) {
          loadChart();
          setHasTriggeredLoad(true);
          // Disconnect observer immediately after triggering
          observer.disconnect();
        }
      },
      {
        threshold: 0.1, // Trigger when 10% of the chart is visible
        rootMargin: '50px', // Start loading 50px before it comes into view
      }
    );

    if (chartRef.current) {
      observer.observe(chartRef.current);
    }

    return () => {
      observer.disconnect();
    };
  }, [autoLoad, hasTriggeredLoad, chartData]);

  // Separate effect to clean up observer when chart is loaded
  React.useEffect(() => {
    if (chartData && hasTriggeredLoad) {
      // Chart is loaded, no need for observer anymore
      return;
    }
  }, [chartData, hasTriggeredLoad]);

    return (
      <div ref={chartRef} className="flex flex-col lg:flex-row gap-6 -mx-3 sm:mx-0">
        {/* Chart Box - 50% width on desktop */}
        <div className="w-full lg:w-1/2 overflow-hidden">
          {/* Chart Section */}
          <div className="pt-3 px-1 pb-0.5 sm:pt-4 sm:px-2 sm:pb-1 border border-border-default">
            <div className="w-full" style={{ height: width < 640 ? '240px' : width < 1024 ? '300px' : '320px' }}>
              {!chartData && !isLoading && !error && (
                <div className="h-full flex items-center justify-center">
                  <div className="flex flex-col items-center">
                    <div className="animate-pulse rounded-full h-8 w-8 bg-spotify/20"></div>
                    <p className="mt-4 text-sm text-text-secondary">Chart will load when visible...</p>
                  </div>
                </div>
              )}
              
              {isLoading && (
                <div className="h-full flex items-center justify-center">
                  <div className="flex flex-col items-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-spotify"></div>
                    <p className="mt-4 text-sm text-text-secondary">Loading chart...</p>
                  </div>
                </div>
              )}
              
              {error && (
                <div className="h-full flex items-center justify-center">
                  <div className="flex flex-col items-center">
                    <p className="text-red-400 text-sm">{error}</p>
                    <button
                      onClick={loadChart}
                      className="mt-2 px-4 py-2 bg-red-900/20 border border-red-700/30 text-red-300 rounded-lg hover:bg-red-800/20 hover:border-red-600/50 transition-all duration-200"
                    >
                      Retry
                    </button>
                  </div>
                </div>
              )}
              
              {chartData && (
                <Plot
                  data={chartData.data}
                  layout={{
                    ...chartData.layout,
                    autosize: true,
                    height: width < 640 ? 220 : width < 1024 ? 280 : 300,
                    margin: { 
                      l: width < 640 ? 40 : 50,
                      r: width < 640 ? 30 : 40,
                      t: width < 640 ? 30 : 40,
                      b: width < 640 ? 50 : 60
                    },
                    paper_bgcolor: 'rgba(0,0,0,0)',
                    plot_bgcolor: 'rgba(0,0,0,0)',
                    font: {
                      color: 'rgb(255, 255, 255)',
                      family: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, system-ui, sans-serif',
                      size: width < 640 ? 10 : width < 1024 ? 11 : 12
                    },
                    xaxis: {
                      ...chartData.layout.xaxis,
                      color: 'rgb(181, 179, 173)',
                      gridcolor: 'rgb(55, 55, 53)',
                      zerolinecolor: 'rgb(55, 55, 53)',
                      tickfont: {
                        size: width < 640 ? 9 : width < 1024 ? 10 : 11
                      }
                    },
                    yaxis: {
                      ...chartData.layout.yaxis,
                      color: 'rgb(181, 179, 173)',
                      gridcolor: 'rgb(55, 55, 53)',
                      zerolinecolor: 'rgb(55, 55, 53)',
                      tickfont: {
                        size: width < 640 ? 9 : width < 1024 ? 10 : 11
                      }
                    }
                  }}
                  style={{ width: '100%', height: '100%' }}
                  config={{ 
                    displayModeBar: false,
                    responsive: true,
                  }}
                />
              )}
            </div>
          </div>
        </div>
        
        {/* Insights Box - 50% width on desktop, separate box */}
        <div className="w-full lg:w-1/2">
          <ChartInsights 
            insights={chartData?.insights || mockInsights.insights}
            hasInsights={chartData?.has_insights || mockInsights.has_insights}
            title={config.title}
          />
        </div>
      </div>
    );
};

const ChartGrid: React.FC<{ csvData: string }> = ({ csvData }) => {
  // Priority charts for immediate loading (highest hiring impact)
  const priorityChartIds = [
    'wpm-distribution',      // Shows skill level distribution
    'accuracy-distribution', // Shows consistency
    'performance-over-time', // Shows improvement trends
    'daily-performance',     // Shows daily trends
    'rolling-average',       // Shows progression over time  
    'rank-distribution'      // Shows competitive performance
  ];

  return (
    <div className="space-y-12">
      {chartConfigs.map((config, index) => (
        <div key={config.id}>
          <ChartCard
            config={config}
            csvData={csvData}
            autoLoad={priorityChartIds.includes(config.id)}
          />
          {index < chartConfigs.length - 1 && (
            <div className="flex justify-center mt-12">
              <div className="w-2/3 border-t-2 border-gray-400"></div>
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export default ChartGrid;