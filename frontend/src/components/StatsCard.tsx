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
    <div className="p-8">
      <div>
        <p className="text-lg font-medium text-text-secondary">{title}</p>
        <p className="text-4xl font-bold text-text-primary mt-4 text-glow-white">{value}</p>
        <p className="text-sm text-text-secondary mt-2">{description}</p>
      </div>
    </div>
  );
};

export default StatsCard;