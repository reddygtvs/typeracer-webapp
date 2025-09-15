#!/usr/bin/env python3
"""
Check only the data arrays between Python and Rust
"""
import requests
import json

def check_data_only():
    # Load sample data
    with open('../frontend/public/sample-data.csv', 'r') as f:
        csv_data = f.read()
    
    chart = 'wpm-distribution'
    
    # Get responses
    python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                  json={"csv_data": csv_data}, timeout=10)
    rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                json={"csv_data": csv_data}, timeout=10)
    
    python_data = python_response.json()
    rust_data = rust_response.json()
    
    print("=== DATA COMPARISON ===")
    
    # Check data arrays
    py_trace = python_data['data'][0]
    rust_trace = rust_data['data'][0]
    
    print(f"Python data length: {len(py_trace['x'])}")
    print(f"Rust data length: {len(rust_trace['x'])}")
    
    print(f"Python x values (first 10): {py_trace['x'][:10]}")
    print(f"Rust x values (first 10): {rust_trace['x'][:10]}")
    
    print(f"Python x types: {[type(x) for x in py_trace['x'][:3]]}")
    print(f"Rust x types: {[type(x) for x in rust_trace['x'][:3]]}")
    
    # Check if values are the same (ignoring type)
    values_match = [int(p) == int(r) for p, r in zip(py_trace['x'][:10], rust_trace['x'][:10])]
    print(f"Values match (ignoring type): {all(values_match)}")

if __name__ == "__main__":
    check_data_only()