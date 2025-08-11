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
                onFileUpload={handleFileUpload}
                onSampleData={handleSampleData}
                loading={loading}
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