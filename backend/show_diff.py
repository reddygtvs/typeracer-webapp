#!/usr/bin/env python3
"""
Show exact differences between Python and Rust outputs
"""
import requests
import json
from deepdiff import DeepDiff

def show_differences():
    # Load sample data
    with open('../frontend/public/sample-data.csv', 'r') as f:
        csv_data = f.read()
    
    chart = 'wpm-distribution'
    print(f"Exact differences for {chart}:")
    
    # Get responses
    python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                  json={"csv_data": csv_data}, timeout=10)
    rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                json={"csv_data": csv_data}, timeout=10)
    
    python_data = python_response.json()
    rust_data = rust_response.json()
    
    # Show detailed differences
    diff = DeepDiff(python_data, rust_data, ignore_order=False, verbose_level=2)
    
    print("All differences:")
    for diff_type, changes in diff.items():
        print(f"\n{diff_type}:")
        if isinstance(changes, dict):
            for key, value in changes.items():
                print(f"  {key}: {value}")
        else:
            print(f"  {changes}")

if __name__ == "__main__":
    show_differences()