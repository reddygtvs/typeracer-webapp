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
    <div className="p-6">
      <div>
        <p className="text-sm font-medium text-text-secondary">{title}</p>
        <p className="text-2xl font-bold text-text-primary mt-2 text-glow-white">{value}</p>
        <p className="text-xs text-text-secondary mt-1">{description}</p>
      </div>
    </div>
  );
};

export default StatsCard;