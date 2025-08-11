#!/usr/bin/env python3
"""
Benchmark script to measure CSV processing performance before/after optimizations.
Usage: python benchmark.py [sample-data-path]
"""

import asyncio
import time
import statistics
import requests
import json
import sys
from pathlib import Path

# Chart endpoints to benchmark
CHART_ENDPOINTS = [
    'wpm-distribution',
    'performance-over-time', 
    'rolling-average',
    'rank-distribution',
    'hourly-performance',
    'accuracy-distribution',
    'daily-performance',
    'wmp-vs-accuracy',
    'win-rate-monthly',
    'top-texts',
    'consistency-score',
    'accuracy-by-rank',
    'cumulative-accuracy',
    'wmp-by-rank-boxplot',
    'racers-impact'
]

class Benchmark:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.csv_data = None
        
    def load_sample_data(self, csv_path=None):
        """Load sample CSV data"""
        if csv_path:
            with open(csv_path, 'r') as f:
                self.csv_data = f.read()
        else:
            # Try to find sample data in common locations
            possible_paths = [
                Path('../frontend/public/sample-data.csv'),
                Path('sample-data.csv'),
                Path('../sample-data.csv')
            ]
            
            for path in possible_paths:
                if path.exists():
                    with open(path, 'r') as f:
                        self.csv_data = f.read()
                    print(f"Loaded sample data from: {path}")
                    break
            else:
                raise FileNotFoundError("Could not find sample-data.csv")
                
        print(f"CSV data size: {len(self.csv_data):,} characters")
        
    def benchmark_stats(self, runs=3):
        """Benchmark the /stats endpoint"""
        times = []
        
        for i in range(runs):
            start = time.perf_counter()
            response = requests.post(f"{self.base_url}/stats", 
                                   json={"csv_data": self.csv_data},
                                   timeout=60)
            end = time.perf_counter()
            
            if response.status_code != 200:
                raise Exception(f"Stats endpoint failed: {response.text}")
                
            times.append(end - start)
            print(f"Stats run {i+1}: {times[-1]:.2f}s")
            
        return {
            'endpoint': 'stats',
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'times': times
        }
    
    def benchmark_chart(self, chart_name, runs=3):
        """Benchmark a specific chart endpoint"""
        times = []
        
        for i in range(runs):
            start = time.perf_counter()
            response = requests.post(f"{self.base_url}/charts/{chart_name}",
                                   json={"csv_data": self.csv_data},
                                   timeout=60)
            end = time.perf_counter()
            
            if response.status_code != 200:
                print(f"Chart {chart_name} failed: {response.text}")
                continue
                
            times.append(end - start)
            
        if not times:
            return None
            
        return {
            'endpoint': f'charts/{chart_name}',
            'mean': statistics.mean(times),
            'median': statistics.median(times), 
            'min': min(times),
            'max': max(times),
            'times': times
        }
    
    def benchmark_all_charts(self, runs=2):
        """Benchmark all chart endpoints"""
        results = []
        total_start = time.perf_counter()
        
        for chart_name in CHART_ENDPOINTS:
            print(f"\nBenchmarking {chart_name}...")
            result = self.benchmark_chart(chart_name, runs)
            if result:
                results.append(result)
                print(f"  Mean: {result['mean']:.2f}s")
            else:
                print(f"  FAILED")
                
        total_end = time.perf_counter()
        
        return {
            'total_time': total_end - total_start,
            'chart_results': results,
            'total_requests': len(results) * runs
        }
    
    def run_full_benchmark(self, runs=2):
        """Run complete benchmark suite"""
        print("=== TYPERACER ANALYTICS BENCHMARK ===")
        print(f"Base URL: {self.base_url}")
        print(f"Runs per endpoint: {runs}")
        
        # Test server connectivity
        try:
            health = requests.get(f"{self.base_url}/health", timeout=5)
            if health.status_code != 200:
                raise Exception("Server not healthy")
        except Exception as e:
            print(f"ERROR: Cannot connect to server at {self.base_url}")
            print(f"Make sure the backend is running: cd backend && python main.py")
            return None
            
        results = {}
        
        # Benchmark stats endpoint
        print("\n--- Stats Endpoint ---")
        results['stats'] = self.benchmark_stats(runs)
        
        # Benchmark all charts
        print("\n--- Chart Endpoints ---")
        results['charts'] = self.benchmark_all_charts(runs)
        
        # Summary
        print("\n=== BENCHMARK SUMMARY ===")
        print(f"Stats endpoint: {results['stats']['mean']:.2f}s avg")
        
        chart_times = [r['mean'] for r in results['charts']['chart_results']]
        if chart_times:
            print(f"Charts avg time: {statistics.mean(chart_times):.2f}s")
            print(f"Charts total time: {results['charts']['total_time']:.2f}s")
            print(f"Slowest chart: {max(chart_times):.2f}s")
            print(f"Fastest chart: {min(chart_times):.2f}s")
        
        # Save results
        timestamp = int(time.time())
        results_file = f"benchmark_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\nResults saved to: {results_file}")
        
        return results

def main():
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    benchmark = Benchmark()
    
    try:
        benchmark.load_sample_data(csv_path)
        results = benchmark.run_full_benchmark()
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()