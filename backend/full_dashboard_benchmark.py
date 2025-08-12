#!/usr/bin/env python3
"""
Full Dashboard Load Benchmark - Simulates real user experience loading all charts
"""

import asyncio
import time
import statistics
import requests
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# All chart endpoints for full dashboard
DASHBOARD_CHARTS = [
    'wpm-distribution',
    'performance-over-time', 
    'rolling-average',
    'rank-distribution',
    'hourly-performance',
    'accuracy-distribution',
    'daily-performance',
    'win-rate-monthly',
    'top-texts',
    'consistency-score',
    'accuracy-by-rank',
    'cumulative-accuracy',
    'racers-impact'
]

class FullDashboardBenchmark:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.csv_data = None
        
    def load_sample_data(self):
        """Load sample CSV data"""
        possible_paths = [
            Path('../frontend/public/sample-data.csv'),
            Path('sample-data.csv'),
            Path('../sample-data.csv')
        ]
        
        for path in possible_paths:
            if path.exists():
                with open(path, 'r') as f:
                    self.csv_data = f.read()
                print(f"✅ Loaded sample data: {len(self.csv_data):,} characters")
                return
                
        raise FileNotFoundError("Could not find sample-data.csv")
    
    def load_single_chart(self, chart_name):
        """Load a single chart and measure time"""
        start = time.perf_counter()
        try:
            response = requests.post(f"{self.base_url}/charts/{chart_name}",
                                   json={"csv_data": self.csv_data},
                                   timeout=30)
            end = time.perf_counter()
            
            if response.status_code == 200:
                return {
                    'chart': chart_name,
                    'time': end - start,
                    'success': True,
                    'error': None
                }
            else:
                return {
                    'chart': chart_name,
                    'time': end - start,
                    'success': False,
                    'error': f"HTTP {response.status_code}"
                }
        except Exception as e:
            end = time.perf_counter()
            return {
                'chart': chart_name,
                'time': end - start,
                'success': False,
                'error': str(e)
            }
    
    def simulate_sequential_load(self):
        """Simulate user loading charts one by one (normal behavior)"""
        print("\n🔄 SEQUENTIAL LOAD (Normal User Behavior)")
        print("=" * 50)
        
        total_start = time.perf_counter()
        results = []
        
        # First, load stats (always happens first)
        print("Loading stats...")
        stats_start = time.perf_counter()
        response = requests.post(f"{self.base_url}/stats", 
                               json={"csv_data": self.csv_data})
        stats_end = time.perf_counter()
        stats_time = stats_end - stats_start
        print(f"  Stats loaded: {stats_time:.3f}s")
        
        # Then load charts sequentially
        for i, chart_name in enumerate(DASHBOARD_CHARTS):
            print(f"Loading chart {i+1}/{len(DASHBOARD_CHARTS)}: {chart_name}...")
            result = self.load_single_chart(chart_name)
            results.append(result)
            
            if result['success']:
                print(f"  ✅ {chart_name}: {result['time']:.3f}s")
            else:
                print(f"  ❌ {chart_name}: {result['time']:.3f}s - {result['error']}")
        
        total_end = time.perf_counter()
        total_time = total_end - total_start
        
        successful_charts = [r for r in results if r['success']]
        failed_charts = [r for r in results if not r['success']]
        
        print(f"\n📊 SEQUENTIAL LOAD RESULTS:")
        print(f"Stats time: {stats_time:.3f}s")
        print(f"Charts loaded: {len(successful_charts)}/{len(DASHBOARD_CHARTS)}")
        print(f"Total dashboard time: {total_time:.3f}s")
        print(f"Average chart time: {statistics.mean([r['time'] for r in successful_charts]):.3f}s")
        print(f"Fastest chart: {min([r['time'] for r in successful_charts]):.3f}s")
        print(f"Slowest chart: {max([r['time'] for r in successful_charts]):.3f}s")
        
        if failed_charts:
            print(f"Failed charts: {[r['chart'] for r in failed_charts]}")
            
        return {
            'total_time': total_time,
            'stats_time': stats_time,
            'chart_results': results,
            'successful_charts': len(successful_charts),
            'failed_charts': len(failed_charts)
        }
    
    def simulate_parallel_load(self):
        """Simulate aggressive parallel loading (power user/pre-loading)"""
        print("\n⚡ PARALLEL LOAD (Aggressive Pre-loading)")
        print("=" * 50)
        
        total_start = time.perf_counter()
        
        # Load stats first
        print("Loading stats...")
        stats_start = time.perf_counter()
        response = requests.post(f"{self.base_url}/stats", 
                               json={"csv_data": self.csv_data})
        stats_end = time.perf_counter()
        stats_time = stats_end - stats_start
        print(f"  Stats loaded: {stats_time:.3f}s")
        
        # Load all charts in parallel
        print(f"Loading {len(DASHBOARD_CHARTS)} charts in parallel...")
        
        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit all chart requests
            futures = {
                executor.submit(self.load_single_chart, chart): chart 
                for chart in DASHBOARD_CHARTS
            }
            
            results = []
            for future in as_completed(futures):
                chart_name = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    if result['success']:
                        print(f"  ✅ {result['chart']}: {result['time']:.3f}s")
                    else:
                        print(f"  ❌ {result['chart']}: {result['time']:.3f}s - {result['error']}")
                        
                except Exception as exc:
                    print(f"  ❌ {chart_name}: Exception - {exc}")
                    results.append({
                        'chart': chart_name,
                        'time': 0,
                        'success': False,
                        'error': str(exc)
                    })
        
        total_end = time.perf_counter()
        total_time = total_end - total_start
        
        successful_charts = [r for r in results if r['success']]
        failed_charts = [r for r in results if not r['success']]
        
        print(f"\n📊 PARALLEL LOAD RESULTS:")
        print(f"Stats time: {stats_time:.3f}s")
        print(f"Charts loaded: {len(successful_charts)}/{len(DASHBOARD_CHARTS)}")
        print(f"Total dashboard time: {total_time:.3f}s")
        print(f"Average chart time: {statistics.mean([r['time'] for r in successful_charts]):.3f}s")
        print(f"Fastest chart: {min([r['time'] for r in successful_charts]):.3f}s")
        print(f"Slowest chart: {max([r['time'] for r in successful_charts]):.3f}s")
        print(f"Parallelization efficiency: {sum([r['time'] for r in successful_charts]) / total_time:.1f}x")
        
        return {
            'total_time': total_time,
            'stats_time': stats_time,
            'chart_results': results,
            'successful_charts': len(successful_charts),
            'failed_charts': len(failed_charts),
            'parallelization_factor': sum([r['time'] for r in successful_charts]) / total_time
        }
    
    def run_cache_warming_test(self):
        """Test the effect of our caching - load dashboard twice"""
        print("\n🔥 CACHE WARMING TEST")
        print("=" * 50)
        
        print("🥶 COLD CACHE (First Load):")
        cold_results = self.simulate_sequential_load()
        
        print("\n🔥 WARM CACHE (Second Load - Should be much faster!):")
        warm_results = self.simulate_sequential_load()
        
        print(f"\n🚀 CACHE EFFECTIVENESS:")
        print(f"Cold cache time: {cold_results['total_time']:.3f}s")
        print(f"Warm cache time: {warm_results['total_time']:.3f}s")
        cache_speedup = cold_results['total_time'] / warm_results['total_time']
        print(f"Cache speedup: {cache_speedup:.1f}x faster!")
        
        return {
            'cold_cache': cold_results,
            'warm_cache': warm_results,
            'cache_speedup': cache_speedup
        }

def main():
    benchmark = FullDashboardBenchmark()
    
    try:
        # Test server connectivity
        health = requests.get("http://localhost:8000/health", timeout=5)
        if health.status_code != 200:
            raise Exception("Server not healthy")
    except Exception as e:
        print(f"❌ ERROR: Cannot connect to server at http://localhost:8000")
        print(f"Make sure the backend is running: python3.11 main.py")
        return
    
    print("🚀 FULL DASHBOARD LOAD BENCHMARK")
    print("=" * 60)
    
    benchmark.load_sample_data()
    
    # Run all benchmark scenarios
    print("\n1️⃣ Testing sequential load (normal user behavior)...")
    sequential_results = benchmark.simulate_sequential_load()
    
    print("\n2️⃣ Testing parallel load (aggressive pre-loading)...")
    parallel_results = benchmark.simulate_parallel_load()
    
    print("\n3️⃣ Testing cache effectiveness...")
    cache_results = benchmark.run_cache_warming_test()
    
    # Final summary
    print("\n🎯 FINAL PERFORMANCE SUMMARY")
    print("=" * 60)
    print(f"📱 Normal user experience: {sequential_results['total_time']:.2f}s")
    print(f"⚡ Parallel loading: {parallel_results['total_time']:.2f}s")
    print(f"🔥 With warm cache: {cache_results['warm_cache']['total_time']:.2f}s")
    print(f"🚀 Cache speedup: {cache_results['cache_speedup']:.1f}x")
    print(f"⚡ Parallel efficiency: {parallel_results.get('parallelization_factor', 1):.1f}x")
    
    # Save detailed results
    timestamp = int(time.time())
    results_file = f"full_dashboard_benchmark_{timestamp}.json"
    all_results = {
        'sequential': sequential_results,
        'parallel': parallel_results,
        'cache_test': cache_results,
        'timestamp': timestamp
    }
    
    with open(results_file, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    print(f"\n📊 Detailed results saved to: {results_file}")

if __name__ == "__main__":
    main()