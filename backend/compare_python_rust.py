#!/usr/bin/env python3
"""
Compare Python vs Rust backend outputs for compatibility
"""
import requests
import json
import deepdiff

# Test the working charts
WORKING_CHARTS = [
    'wpm-distribution',
    'accuracy-distribution', 
    'performance-over-time',
    'rank-distribution',
    'hourly-performance',
    'wpm-vs-accuracy',
    'win-rate-monthly',
    'accuracy-by-rank',
    'cumulative-accuracy',
    'wpm-by-rank-boxplot',
    'racers-impact',
    'frequent-texts-improvement',
    'top-texts-distribution',
    'win-rate-after-win',
    'fastest-slowest-races',
    'time-between-races'
]

def compare_outputs():
    # Load sample data (smaller for faster comparison)
    with open('../frontend/public/sample-data.csv', 'r') as f:
        csv_data = f.read()
    
    print(f"Comparing Python vs Rust outputs for {len(WORKING_CHARTS)} charts...")
    print("=" * 60)
    
    identical = []
    different = []
    
    for i, chart in enumerate(WORKING_CHARTS):
        print(f"Comparing {i+1}/{len(WORKING_CHARTS)}: {chart}...")
        
        try:
            # Get Python response (port 8001)
            python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                          json={"csv_data": csv_data},
                                          timeout=10)
            
            # Get Rust response (port 8000) 
            rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                        json={"csv_data": csv_data},
                                        timeout=10)
            
            if python_response.status_code != 200:
                print(f"  ❌ Python failed: HTTP {python_response.status_code}")
                different.append(f"{chart} (Python failed)")
                continue
                
            if rust_response.status_code != 200:
                print(f"  ❌ Rust failed: HTTP {rust_response.status_code}")
                different.append(f"{chart} (Rust failed)")
                continue
            
            python_data = python_response.json()
            rust_data = rust_response.json()
            
            # Compare the outputs
            diff = deepdiff.DeepDiff(python_data, rust_data, ignore_order=True)
            
            if not diff:
                print(f"  ✅ {chart}: IDENTICAL")
                identical.append(chart)
            else:
                print(f"  ⚠️  {chart}: DIFFERENT")
                print(f"      Differences: {len(diff)} keys differ")
                different.append(chart)
                
        except Exception as e:
            print(f"  ❌ {chart}: ERROR - {str(e)}")
            different.append(f"{chart} (Error)")
    
    print("\n" + "=" * 60)
    print(f"COMPATIBILITY RESULTS:")
    print(f"Identical outputs: {len(identical)}/{len(WORKING_CHARTS)} ({len(identical)/len(WORKING_CHARTS)*100:.1f}%)")
    print(f"Identical: {identical}")
    print(f"Different: {different}")

if __name__ == "__main__":
    compare_outputs()