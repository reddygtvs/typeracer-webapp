#!/usr/bin/env python3
"""
Check what insights actually are
"""
import requests
import json

def check_insights():
    # Load race data
    with open('race_data.csv', 'r') as f:
        csv_data = f.read()
    
    chart = 'hourly-performance'
    
    # Get responses
    python_response = requests.post(f"http://localhost:8001/charts/{chart}",
                                  json={"csv_data": csv_data}, timeout=30)
    rust_response = requests.post(f"http://localhost:8000/charts/{chart}",
                                json={"csv_data": csv_data}, timeout=30)
    
    py_data = python_response.json()
    rust_data = rust_response.json()
    
    print("PYTHON INSIGHTS:")
    for i, insight in enumerate(py_data.get('insights', [])):
        print(f"{i+1}. {insight}")
    
    print(f"\nRUST INSIGHTS:")
    for i, insight in enumerate(rust_data.get('insights', [])):
        print(f"{i+1}. {insight}")

if __name__ == "__main__":
    check_insights()