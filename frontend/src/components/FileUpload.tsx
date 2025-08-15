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
    <div className="w-full space-y-6">
      <div
        {...getRootProps()}
        className={`glass rounded-xl p-8 text-center cursor-pointer transition-all duration-300 hover-glow-green ${
          isDragActive
            ? 'border-green-400/40 bg-green-400/5'
            : 'hover:border-green-400/20'
        } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input {...getInputProps()} />
        
        {loading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-400"></div>
            <p className="mt-4 text-premium-sm text-white/70">Processing your data...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full glass-strong mb-4">
              {isDragActive ? (
                <Upload className="h-8 w-8 text-green-400" />
              ) : (
                <FileText className="h-8 w-8 text-white/70" />
              )}
            </div>
            <h3 className="text-premium-lg font-medium text-white mb-2">
              {isDragActive ? 'Drop your CSV file here' : 'Upload race data CSV'}
            </h3>
            <p className="text-premium-sm text-white/60">
              Drag and drop your TypeRacer CSV file, or click to browse
            </p>
          </div>
        )}
      </div>

      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-white/10" />
        </div>
        <div className="relative flex justify-center">
          <span className="bg-black px-4 text-premium-sm text-white/60 uppercase tracking-wider">
            Or try demo data
          </span>
        </div>
      </div>

      <button
        onClick={handleSampleData}
        disabled={loading}
        className={`btn-premium btn-premium-lg btn-green w-full ${
          loading ? 'opacity-50 cursor-not-allowed' : ''
        }`}
      >
        <Database className="h-5 w-5 mr-3" />
        Explore Sample Dataset
      </button>
      
      <div className="text-center space-y-2">
        <p className="text-premium-sm text-green-400/80 font-medium">
          34,617 sample race records included
        </p>
        <p className="text-premium-xs text-white/50">
          Expected format: Race #, WPM, Accuracy, Rank, # Racers, Text ID, Date/Time (UTC)
        </p>
      </div>
    </div>
  );
};

export default FileUpload;