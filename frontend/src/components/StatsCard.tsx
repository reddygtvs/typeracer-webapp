import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  description: string;
  color: 'blue' | 'green' | 'yellow' | 'purple';
}

const colorVariants = {
  blue: 'bg-hover-bg text-spotify border-border-default',
  green: 'bg-hover-bg text-spotify border-border-default',
  yellow: 'bg-hover-bg text-spotify border-border-default',
  purple: 'bg-hover-bg text-spotify border-border-default',
};

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, description, color }) => {
  return (
    <div className="bg-bg-primary rounded-lg border border-border-default p-6 hover:border-border-hover transition-all duration-200">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm font-medium text-text-secondary">{title}</p>
          <p className="text-2xl font-bold text-text-primary mt-2 text-glow-white">{value}</p>
          <p className="text-xs text-text-secondary mt-1">{description}</p>
        </div>
        <div className={`p-3 rounded-lg border ${colorVariants[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </div>
  );
};

export default StatsCard;