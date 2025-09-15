#!/usr/bin/env python3
"""
Show detailed differences for all charts
"""
import requests
import json
from deepdiff import DeepDiff

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

def analyze_differences():
    # Load race data
    with open('race_data.csv', 'r') as f:
        csv_data = f.read()
    
    print("DETAILED DIFFERENCES ANALYSIS")
    print("=" * 50)
    
    for chart in WORKING_CHARTS[:3]:  # Just first 3 to see pattern
        print(f"\n--- {chart} ---")
        
        # Get responses
        python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                      json={"csv_data": csv_data}, timeout=30)
        rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                    json={"csv_data": csv_data}, timeout=30)
        
        if python_response.status_code != 200 or rust_response.status_code != 200:
            print(f"ERROR: Python {python_response.status_code}, Rust {rust_response.status_code}")
            continue
            
        python_data = python_response.json()
        rust_data = rust_response.json()
        
        # Compare keys
        py_keys = set(python_data.keys())
        rust_keys = set(rust_data.keys())
        
        print(f"Python keys: {py_keys}")
        print(f"Rust keys: {rust_keys}")
        print(f"Missing in Rust: {py_keys - rust_keys}")
        print(f"Extra in Rust: {rust_keys - py_keys}")
        
        # Compare data structure
        if 'data' in python_data and 'data' in rust_data:
            py_data_len = len(python_data['data'][0]['x']) if len(python_data['data']) > 0 and 'x' in python_data['data'][0] else 0
            rust_data_len = len(rust_data['data'][0]['x']) if len(rust_data['data']) > 0 and 'x' in rust_data['data'][0] else 0
            print(f"Data array lengths: Python {py_data_len}, Rust {rust_data_len}")
            
            if py_data_len > 0 and rust_data_len > 0:
                py_sample = python_data['data'][0]['x'][:3]
                rust_sample = rust_data['data'][0]['x'][:3]
                print(f"Sample data: Python {py_sample}, Rust {rust_sample}")
        
        # Compare insights
        py_insights = len(python_data.get('insights', []))
        rust_insights = len(rust_data.get('insights', []))
        print(f"Insights count: Python {py_insights}, Rust {rust_insights}")

if __name__ == "__main__":
    analyze_differences()