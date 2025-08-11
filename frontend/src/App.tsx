import React, { useState, useCallback } from 'react';
import { Upload, BarChart3, TrendingUp } from 'lucide-react';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import { RaceData } from './types';

function App() {
  const [data, setData] = useState<RaceData | null>(null);
  const [loading, setLoading] = useState(false);

  const handleDataUpload = useCallback((uploadedData: RaceData) => {
    setData(uploadedData);
    setLoading(false);
  }, []);

  const handleReset = useCallback(() => {
    setData(null);
    setLoading(false);
  }, []);

  return (
    <div className="min-h-screen bg-black">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-5 pt-3 pb-3">
          <div className="flex justify-between items-center">
            <h1 
              className="text-sm sm:text-xl md:text-2xl font-bold text-white uppercase tracking-widest m-0 text-glow-white cursor-pointer hover:text-spotify transition-colors duration-200"
              onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
            >
              TYPERACER ANALYTICS<span className="bounce-favicon">.</span>
            </h1>
            
            {data && (
              <button
                onClick={handleReset}
                className="inline-flex items-center px-3 py-1.5 sm:px-4 sm:py-2 border border-border-default rounded-md text-xs sm:text-sm font-medium text-text-secondary bg-transparent hover:bg-hover-bg hover:border-border-hover hover:text-text-accent transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-spotify focus:ring-offset-2 focus:ring-offset-black"
              >
                <Upload className="h-4 w-4 mr-2" />
                Upload New Data
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20 max-w-5xl mx-auto px-5 py-8">
        {!data ? (
          <div className="min-h-[600px] flex flex-col items-center justify-center animate-fade-in">
            <div className="max-w-md w-full">
              <div className="text-center mb-8">
                <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-bg-primary mb-4 border border-border-default">
                  <BarChart3 className="h-8 w-8 text-spotify" />
                </div>
                <h2 className="text-2xl font-bold text-text-primary mb-2 text-glow-white">
                  Welcome to TypeRacer Analytics
                </h2>
                <p className="text-text-secondary">
                  Upload your race data CSV file or try the sample data
                </p>
              </div>
              
              <FileUpload 
                onUpload={handleDataUpload}
                loading={loading}
                setLoading={setLoading}
              />
            </div>
          </div>
        ) : (
          <Dashboard data={data} />
        )}
      </main>
    </div>
  );
}

export default App;