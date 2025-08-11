import React from 'react';
import { Lightbulb, TrendingUp, Info } from 'lucide-react';

interface ChartInsightsProps {
  insights: string[];
  hasInsights: boolean;
  title: string;
}

const ChartInsights: React.FC<ChartInsightsProps> = ({ insights, hasInsights, title }) => {
  return (
    <div className="p-4 h-full">
      <div className="flex items-center space-x-2 mb-4">
        <h4 className="text-lg font-semibold text-text-primary">Insights</h4>
      </div>
      
      <div className="space-y-3">
        {hasInsights ? (
          insights.map((insight, index) => (
            <div key={index} className="flex items-start space-x-3">
              <div className="flex-shrink-0 text-spotify">
                &gt;
              </div>
              <p className="text-sm lg:text-base text-text-secondary leading-relaxed">
                {insight}
              </p>
            </div>
          ))
        ) : (
          <div className="flex items-start space-x-3">
            <Info className="h-4 w-4 text-text-tertiary mt-0.5 flex-shrink-0" />
            <p className="text-sm lg:text-base text-text-tertiary leading-relaxed">
              Upload more data to see detailed insights for this chart
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChartInsights;