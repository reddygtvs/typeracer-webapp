import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, Database } from 'lucide-react';
import { uploadData, useSampleData } from '../utils/api';
import { RaceData } from '../types';

interface FileUploadProps {
  onUpload: (data: RaceData) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

const FileUpload: React.FC<FileUploadProps> = ({ onUpload, loading, setLoading }) => {
  const [error, setError] = React.useState<string | null>(null);

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (!file) return;

    setLoading(true);
    setError(null);

    try {
      const response = await uploadData(file);
      onUpload(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload file');
      setLoading(false);
    }
  }, [onUpload, setLoading]);

  const handleUseSampleData = useCallback(async () => {
    setLoading(true);
    setError(null);

    try {
      const response = await useSampleData();
      onUpload(response);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load sample data');
      setLoading(false);
    }
  }, [onUpload, setLoading]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv']
    },
    maxFiles: 1,
    disabled: loading
  });

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`relative border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all duration-200 ${
          isDragActive
            ? 'border-spotify bg-spotify/5'
            : 'border-border-default hover:border-border-hover'
        } ${loading ? 'opacity-50 cursor-not-allowed' : ''} bg-bg-primary`}
      >
        <input {...getInputProps()} />
        
        {loading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-spotify"></div>
            <p className="mt-4 text-sm text-text-secondary">Processing your data...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-hover-bg border border-border-default">
              {isDragActive ? (
                <Upload className="h-6 w-6 text-spotify" />
              ) : (
                <FileText className="h-6 w-6 text-text-secondary" />
              )}
            </div>
            <p className="mt-4 text-sm font-medium text-text-primary">
              {isDragActive ? 'Drop your CSV file here' : 'Upload race data CSV'}
            </p>
            <p className="mt-1 text-xs text-text-secondary">
              Drag and drop your TypeRacer CSV file, or click to browse
            </p>
          </div>
        )}
      </div>

      {error && (
        <div className="mt-4 p-4 bg-red-900/20 border border-red-700/30 rounded-md">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-400" />
            <div className="ml-3">
              <p className="text-sm font-medium text-red-300">Upload failed</p>
              <p className="text-sm text-red-400 mt-1">{error}</p>
            </div>
          </div>
        </div>
      )}

      <div className="mt-6">
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-default" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-black px-2 text-text-secondary">Or</span>
          </div>
        </div>

        <div className="mt-6">
          <button
            onClick={handleUseSampleData}
            disabled={loading}
            className={`w-full flex items-center justify-center px-4 py-3 border border-border-default rounded-md bg-transparent text-sm font-medium text-text-secondary hover:bg-hover-bg hover:border-border-hover hover:text-text-accent transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-spotify focus:ring-offset-2 focus:ring-offset-black ${
              loading ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            <Database className="h-4 w-4 mr-2" />
            Use Sample Data
          </button>
          <p className="mt-2 text-xs text-text-secondary text-center">
            Try the demo with 34,617 sample race records
          </p>
        </div>

        <div className="mt-4 text-center">
          <p className="text-xs text-text-secondary">
            Expected format: Race #, WPM, Accuracy, Rank, # Racers, Text ID, Date/Time (UTC)
          </p>
        </div>
      </div>
    </div>
  );
};

export default FileUpload;