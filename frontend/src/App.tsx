import {
  useState,
  useCallback,
  useEffect,
  useRef,
  Suspense,
  lazy,
} from "react";
import { Upload, BarChart3 } from "lucide-react";
import FileUpload from "./components/FileUpload";
const Dashboard = lazy(() => import("./components/Dashboard"));
import { RaceData } from "./types";
import { getStats } from "./utils/api";

function App() {
  const [data, setData] = useState<RaceData | null>(null);
  const [loading, setLoading] = useState(false);

  const requestVersion = useRef(0);
  const [error, setError] = useState("");
  const clearSavedData = () => {
    try {
      for (const key of [
        "typeracer-csv",
        "typeracer-stats",
        "typeracer-source",
      ])
        localStorage.removeItem(key);
    } catch {
      /* Storage is optional. */
    }
  };
  const processCSVData = useCallback(
    async (csvData: string, source: string, version: number) => {
      if (version !== requestVersion.current) return;
      try {
        const stats = await getStats(csvData);
        if (version !== requestVersion.current) return;
        setData({ stats, csvData });
        try {
          localStorage.setItem("typeracer-csv", csvData);
        } catch {
          /* Valid data remains usable when storage is unavailable. */
        }
      } catch (error) {
        if (version !== requestVersion.current) return;
        setError(
          error instanceof Error
            ? error.message
            : "Could not process this CSV.",
        );
        if (source === "restored") clearSavedData();
      } finally {
        if (version === requestVersion.current) setLoading(false);
      }
    },
    [],
  );

  const handleFileUpload = useCallback(
    async (file: File) => {
      const version = ++requestVersion.current;
      setError("");
      if (file.size > 20_000_000) {
        setError("CSV exceeds the 20 MB limit.");
        return;
      }
      setLoading(true);
      try {
        await processCSVData(await file.text(), "upload", version);
      } catch {
        if (version === requestVersion.current) {
          setError("Could not read this file.");
          setLoading(false);
        }
      }
    },
    [processCSVData],
  );

  const handleSampleData = useCallback(async () => {
    const version = ++requestVersion.current;
    setError("");
    setLoading(true);
    try {
      const compressed = typeof DecompressionStream !== "undefined";
      const response = await fetch(
        compressed ? "/sample-data.csv.gz" : "/sample-data.csv",
      );
      if (!response.ok) throw new Error("Could not fetch sample data.");
      const csvData =
        compressed &&
        response.body &&
        !response.headers.get("content-encoding")?.includes("gzip")
          ? await new Response(
              response.body.pipeThrough(new DecompressionStream("gzip")),
            ).text()
          : await response.text();
      await processCSVData(csvData, "sample", version);
    } catch {
      if (version === requestVersion.current) {
        setError("Could not load sample data. Please try again.");
        setLoading(false);
      }
    }
  }, [processCSVData]);

  const handleReset = useCallback(() => {
    requestVersion.current++;
    setData(null);
    setLoading(false);
    setError("");
    clearSavedData();
  }, []);

  useEffect(() => {
    let savedCSV: string | null;
    try {
      savedCSV = localStorage.getItem("typeracer-csv");
    } catch {
      return;
    }
    if (savedCSV) {
      setLoading(true);
      void processCSVData(savedCSV, "restored", ++requestVersion.current);
    }
    const request = requestVersion;
    return () => {
      request.current++;
    };
  }, [processCSVData]);

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
                  onClick={() =>
                    window.scrollTo({ top: 0, behavior: "smooth" })
                  }
                >
                  <span className="font-medium text-gradient-green">
                    TypeRacer
                  </span>
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
        {error && (
          <p
            role="alert"
            className="mb-6 rounded border border-red-500/50 bg-red-950/30 p-4 text-red-200"
          >
            {error}
          </p>
        )}
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
            <Suspense fallback={<p>Loading dashboard...</p>}>
              <Dashboard key={data.csvData} data={data} />
            </Suspense>
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
