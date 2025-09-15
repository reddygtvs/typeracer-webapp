#!/usr/bin/env python3
"""
Detailed comparison of Python vs Rust outputs
"""
import requests
import json

def detailed_compare():
    # Load sample data
    with open('../frontend/public/sample-data.csv', 'r') as f:
        csv_data = f.read()
    
    chart = 'wpm-distribution'  # Test one chart in detail
    print(f"Detailed comparison for {chart}...")
    
    # Get Python response
    python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                  json={"csv_data": csv_data},
                                  timeout=10)
    
    # Get Rust response
    rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                json={"csv_data": csv_data},
                                timeout=10)
    
    print(f"Python status: {python_response.status_code}")
    print(f"Rust status: {rust_response.status_code}")
    
    if python_response.status_code == 200 and rust_response.status_code == 200:
        python_data = python_response.json()
        rust_data = rust_response.json()
        
        print("\nPython response keys:", list(python_data.keys()))
        print("Rust response keys:", list(rust_data.keys()))
        
        print("\nPython data structure:")
        for key in python_data.keys():
            print(f"  {key}: {type(python_data[key])}")
            if key == 'data' and isinstance(python_data[key], list) and len(python_data[key]) > 0:
                print(f"    First trace keys: {list(python_data[key][0].keys())}")
        
        print("\nRust data structure:")
        for key in rust_data.keys():
            print(f"  {key}: {type(rust_data[key])}")
            if key == 'data' and isinstance(rust_data[key], list) and len(rust_data[key]) > 0:
                print(f"    First trace keys: {list(rust_data[key][0].keys())}")
        
        print("\nFirst few values comparison:")
        if 'data' in python_data and 'data' in rust_data:
            if len(python_data['data']) > 0 and len(rust_data['data']) > 0:
                py_trace = python_data['data'][0]
                rust_trace = rust_data['data'][0]
                print(f"Python trace type: {py_trace.get('type', 'missing')}")
                print(f"Rust trace type: {rust_trace.get('type', 'missing')}")
                if 'x' in py_trace and 'x' in rust_trace:
                    print(f"Python x (first 5): {py_trace['x'][:5]}")
                    print(f"Rust x (first 5): {rust_trace['x'][:5]}")

if __name__ == "__main__":
    detailed_compare()