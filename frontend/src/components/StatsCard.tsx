import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatsCardProps {
  title: string;
  value: string;
  icon: LucideIcon;
  description: string;
  color: 'blue' | 'green' | 'yellow' | 'purple';
}

const iconColors = {
  blue: 'text-blue-400',
  green: 'text-green-400',
  yellow: 'text-yellow-400',
  purple: 'text-purple-400',
};

const StatsCard: React.FC<StatsCardProps> = ({ title, value, icon: Icon, description, color }) => {
  return (
    <div className="flex items-center justify-between p-6 bg-transparent">
      <div className="flex-1">
        <p className="text-premium-sm font-medium text-white/60 mb-1">{title}</p>
        <p className="text-premium-3xl font-bold text-white mb-1" style={{ letterSpacing: "-0.02em" }}>
          {value}
        </p>
        <p className="text-premium-xs text-white/50">{description}</p>
      </div>
      <div className="ml-6">
        <Icon className={`h-8 w-8 ${iconColors[color]} opacity-80`} strokeWidth={1.5} />
      </div>
    </div>
  );
};

export default StatsCard;