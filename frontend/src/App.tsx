import React, { useState, useCallback, useEffect } from 'react';
import { Upload, BarChart3, TrendingUp } from 'lucide-react';
import FileUpload from './components/FileUpload';
import Dashboard from './components/Dashboard';
import { RaceData } from './types';
import { getStats } from './utils/api';

function App() {
  const [data, setData] = useState<RaceData | null>(null);
  const [loading, setLoading] = useState(false);

  const processCSVData = async (csvData: string, source: string) => {
    setLoading(true);
    try {
      const stats = await getStats(csvData);
      const raceData: RaceData = { stats, csvData };
      setData(raceData);

      // Optional: Persist to localStorage
      localStorage.setItem('typeracer-csv', csvData);
      localStorage.setItem('typeracer-stats', JSON.stringify(stats));
      localStorage.setItem('typeracer-source', source);
    } catch (error: any) {
      console.error('Failed to process CSV:', error);
      alert(error.response?.data?.detail || 'Failed to process CSV data');
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = useCallback(async (file: File) => {
    // For large files, use streaming approach
    let csvData: string;
    
    if (file.size > 500_000) { // 500KB threshold
      // Stream large files in chunks to avoid blocking UI
      csvData = await streamFileRead(file);
    } else {
      csvData = await file.text();
    }
    
    await processCSVData(csvData, 'upload');
  }, []);

  const streamFileRead = async (file: File): Promise<string> => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        resolve(e.target?.result as string);
      };
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file);
    });
  };

  const handleSampleData = useCallback(async () => {
    try {
      setLoading(true);
      const response = await fetch('/sample-data.csv');
      if (!response.ok) {
        throw new Error('Failed to fetch sample data');
      }
      const csvData = await response.text();
      await processCSVData(csvData, 'sample');
    } catch (error) {
      console.error('Failed to load sample data:', error);
      alert('Failed to load sample data. Make sure sample-data.csv exists in the public folder.');
      setLoading(false);
    }
  }, []);

  const handleReset = useCallback(() => {
    setData(null);
    setLoading(false);
    localStorage.removeItem('typeracer-csv');
    localStorage.removeItem('typeracer-stats');
    localStorage.removeItem('typeracer-source');
  }, []);

  // Restore data on page load
  useEffect(() => {
    const savedCsv = localStorage.getItem('typeracer-csv');
    const savedStats = localStorage.getItem('typeracer-stats');
    if (savedCsv && savedStats) {
      try {
        const stats = JSON.parse(savedStats);
        setData({ csvData: savedCsv, stats });
      } catch (error) {
        console.error('Failed to restore saved data:', error);
        // Clear corrupted data
        localStorage.removeItem('typeracer-csv');
        localStorage.removeItem('typeracer-stats');
        localStorage.removeItem('typeracer-source');
      }
    }
  }, []);

  return (
    <div className="min-h-screen bg-premium">
      {/* Header */}
      <nav className="relative z-10 px-6 py-6">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div
                className="w-7 h-7 rounded-md bg-gradient-to-br from-green-400/90 to-green-500/90 flex items-center justify-center backdrop-blur-sm"
                style={{
                  boxShadow:
                    "0 1px 3px rgba(57, 255, 20, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.15)",
                }}
              >
                <BarChart3 className="h-4 w-4 text-white" />
              </div>
              <div>
                <h1
                  className="text-lg font-light text-white cursor-pointer"
                  style={{ letterSpacing: "-0.01em" }}
                  onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
                >
                  <span className="font-medium text-gradient-green">TypeRacer</span>
                  <span className="text-white/90 font-light">Analytics</span>
                </h1>
              </div>
            </div>
            
            {data && (
              <button
                onClick={handleReset}
                className="glass px-4 py-2.5 rounded-lg hover:border-green-400/20 transition-all duration-200 group"
              >
                <div className="flex items-center space-x-2">
                  <Upload className="h-4 w-4 text-white/70 group-hover:text-white transition-colors" />
                  <span
                    className="text-sm text-white/70 font-light group-hover:text-white transition-colors"
                    style={{ letterSpacing: "-0.01em" }}
                  >
                    Upload New Data
                  </span>
                </div>
              </button>
            )}
          </div>
        </div>
      </nav>

      <main className="max-w-6xl mx-auto px-6 pb-20">
        {!data ? (
          <div className="text-center mb-16 animate-fade-up">
            <div className="inline-flex items-center glass px-4 py-2 rounded-lg mb-6">
              <span className="text-premium-sm font-medium text-green-400 uppercase tracking-wider">
                Performance Analytics Dashboard
              </span>
            </div>

            <h1 className="text-premium-4xl md:text-6xl font-bold text-white mb-6 max-w-4xl mx-auto leading-[1.1]">
              <span className="text-gradient-green">TypeRacer</span> performance
              insights and analytics
            </h1>

            <p className="text-premium-xl text-white/70 max-w-2xl mx-auto leading-relaxed mb-12">
              Upload your race data CSV or explore sample insights to discover
              <span className="text-green-400 font-medium block">
                detailed performance metrics and trends
              </span>
            </p>

            <div className="max-w-md mx-auto animate-fade-up-delay-1">
              <FileUpload
                onFileUpload={handleFileUpload}
                onSampleData={handleSampleData}
                loading={loading}
              />
            </div>
          </div>
        ) : (
          <div className="animate-fade-up">
            <Dashboard data={data} />
          </div>
        )}
      </main>

      {/* Background decorations */}
      <div className="fixed inset-0 -z-10 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-green-500/5 rounded-full blur-3xl"></div>
        <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-green-400/3 rounded-full blur-3xl"></div>
        <div className="absolute top-3/4 left-1/2 w-64 h-64 bg-green-600/4 rounded-full blur-2xl"></div>
      </div>
    </div>
  );
}

export default App;