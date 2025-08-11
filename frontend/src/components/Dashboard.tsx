import React from 'react';
import { Trophy, Target, TrendingUp, Calendar } from 'lucide-react';
import { RaceData } from '../types';
import StatsCard from './StatsCard';
import ChartGrid from './ChartGrid';

interface DashboardProps {
  data: RaceData;
}

const Dashboard: React.FC<DashboardProps> = ({ data }) => {
  const { stats } = data;

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'numeric',
      day: 'numeric'
    });
  };

  const formatNumber = (num: number) => {
    return num.toLocaleString();
  };

  const winRate = ((stats.total_wins / stats.total_races) * 100).toFixed(1);

  return (
    <div className="space-y-8">
      {/* Overview Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <StatsCard
          title="Total Races"
          value={formatNumber(stats.total_races)}
          icon={Calendar}
          description={`From ${formatDate(stats.date_range.start)} to ${formatDate(stats.date_range.end)}`}
          color="blue"
        />
        
        <StatsCard
          title="Average WPM"
          value={Math.round(stats.avg_wpm).toString()}
          icon={TrendingUp}
          description="Words per minute"
          color="green"
        />
        
        <StatsCard
          title="Best Race"
          value={`${stats.best_wpm} WPM`}
          icon={Trophy}
          description={`${winRate}% win rate`}
          color="yellow"
        />
        
        <StatsCard
          title="Accuracy"
          value={`${(stats.avg_accuracy * 100).toFixed(1)}%`}
          icon={Target}
          description="Average accuracy"
          color="purple"
        />
      </div>

      {/* Charts */}
      <div className="py-8">
        <div className="mb-12">
          <h2 className="text-xl font-semibold text-text-primary text-glow-white">Performance Analytics</h2>
          <p className="text-text-secondary text-sm mt-1">
            Interactive visualizations of your typing performance over time
          </p>
        </div>
        
        <ChartGrid csvData={data.csvData} />
      </div>
    </div>
  );
};

export default Dashboard;