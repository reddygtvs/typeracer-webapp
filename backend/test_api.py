#!/usr/bin/env python3
import requests
import json

# Read the CSV file
with open('race_data.csv', 'r') as f:
    csv_content = f.read()

# Test the stats endpoint
print("Testing /stats endpoint...")
response = requests.post('http://localhost:8000/stats', json={
    'csv_data': csv_content
})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Test a chart endpoint
print("\nTesting /charts/wpm-distribution endpoint...")
response = requests.post('http://localhost:8000/charts/wpm-distribution', json={
    'csv_data': csv_content
})

print(f"Status: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"Chart has {len(data.get('data', []))} data elements")
    print(f"Insights available: {data.get('has_insights', False)}")
    if data.get('has_insights'):
        print(f"Number of insights: {len(data.get('insights', []))}")
else:
    print(f"Error: {response.text}")