#!/usr/bin/env python3
"""
Comprehensive comparison of all 19 charts with race_data.csv
"""
import requests
import json

ALL_CHARTS = [
    'wpm-distribution',
    'accuracy-distribution', 
    'performance-over-time',
    'daily-performance',
    'rolling-average',
    'rank-distribution',
    'hourly-performance',
    'wpm-vs-accuracy',
    'win-rate-monthly',
    'top-texts',
    'consistency-score',
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

def compare_all_charts():
    # Load race data
    with open('race_data.csv', 'r') as f:
        csv_data = f.read()
    
    print("COMPREHENSIVE CHART COMPARISON - RACE_DATA.CSV")
    print("=" * 80)
    
    for i, chart in enumerate(ALL_CHARTS):
        print(f"\n{i+1:2d}. {chart}")
        print("-" * 40)
        
        try:
            # Get Python response
            python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                          json={"csv_data": csv_data}, timeout=30)
            
            # Get Rust response  
            rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                        json={"csv_data": csv_data}, timeout=30)
            
            py_status = python_response.status_code
            rust_status = rust_response.status_code
            
            print(f"Status: Python {py_status}, Rust {rust_status}")
            
            if py_status != 200:
                print(f"Python FAILED: {py_status}")
                continue
                
            if rust_status != 200:
                print(f"Rust FAILED: {rust_status}")
                continue
            
            # Both succeeded, compare outputs
            py_data = python_response.json()
            rust_data = rust_response.json()
            
            # Compare data arrays
            if 'data' in py_data and 'data' in rust_data and len(py_data['data']) > 0 and len(rust_data['data']) > 0:
                py_trace = py_data['data'][0]
                rust_trace = rust_data['data'][0]
                
                # Get data arrays
                py_x = py_trace.get('x', [])
                rust_x = rust_trace.get('x', [])
                py_y = py_trace.get('y', [])
                rust_y = rust_trace.get('y', [])
                
                print(f"Data length: Python x={len(py_x)} y={len(py_y)}, Rust x={len(rust_x)} y={len(rust_y)}")
                
                if len(py_x) > 0 and len(rust_x) > 0:
                    print(f"X values: Python {py_x[:3]} ({type(py_x[0])}), Rust {rust_x[:3]} ({type(rust_x[0])})")
                    
                if len(py_y) > 0 and len(rust_y) > 0:
                    print(f"Y values: Python {py_y[:3]} ({type(py_y[0])}), Rust {rust_y[:3]} ({type(rust_y[0])})")
                
                # Check if values match (ignoring type)
                if len(py_x) == len(rust_x) and len(py_x) > 0:
                    x_match = all(str(p) == str(r) for p, r in zip(py_x[:10], rust_x[:10]))
                    print(f"X values match: {x_match}")
                    
                if len(py_y) == len(rust_y) and len(py_y) > 0:
                    y_match = all(str(p) == str(r) for p, r in zip(py_y[:10], rust_y[:10]))
                    print(f"Y values match: {y_match}")
            
            # Compare insights
            py_insights = len(py_data.get('insights', []))
            rust_insights = len(rust_data.get('insights', []))
            print(f"Insights: Python {py_insights}, Rust {rust_insights}")
            
            # Overall match
            if py_data == rust_data:
                print("IDENTICAL ✅")
            else:
                print("DIFFERENT ❌")
            
        except Exception as e:
            print(f"ERROR: {str(e)}")

if __name__ == "__main__":
    compare_all_charts()