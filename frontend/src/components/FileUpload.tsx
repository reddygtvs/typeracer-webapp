import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText, AlertCircle, Database } from 'lucide-react';

interface FileUploadProps {
  onFileUpload: (file: File) => Promise<void>;
  onSampleData: () => Promise<void>;
  loading: boolean;
}

const FileUpload: React.FC<FileUploadProps> = ({
  onFileUpload,
  onSampleData,
  loading
}) => {
  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file) {
      await onFileUpload(file);
    }
  }, [onFileUpload]);

  // Update the sample data button handler:
  const handleSampleData = async () => {
    await onSampleData();
  };

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
            onClick={handleSampleData}
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